/*
 * Copyright 2026 UCP Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.dev.ucp;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.atLeastOnce;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.dev.ucp.service.shopping.model.FulfillmentResponse;
import com.dev.ucp.service.shopping.model.OrderConfirmation;
import com.dev.ucp.service.shopping.model.UCPCheckoutResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Answers;
import org.springframework.web.client.RestClient;

public class OrderWebHookNotifierTest {

  private RestClient.Builder restClientBuilder;
  private RestClient restClient;
  private ObjectMapper objectMapper;
  private ExtensionsHelper extensionsHelper;
  private OrderWebHookNotifier notifier;

  @BeforeEach
  public void setUp() throws Exception {
    restClientBuilder = mock(RestClient.Builder.class);
    restClient = mock(RestClient.class, Answers.RETURNS_DEEP_STUBS);
    objectMapper = mock(ObjectMapper.class);
    extensionsHelper = mock(ExtensionsHelper.class);

    when(restClientBuilder.build()).thenReturn(restClient);
    notifier = new OrderWebHookNotifier(restClientBuilder);

    // Inject mocks into private fields
    setPrivateField(notifier, "objectMapper", objectMapper);
    setPrivateField(notifier, "extensionsHelper", extensionsHelper);
  }

  private void setPrivateField(Object target, String fieldName, Object value) throws Exception {
    var field = target.getClass().getDeclaredField(fieldName);
    field.setAccessible(true);
    field.set(target, value);
  }

  @Test
  public void testNotifyLifecycle() throws Exception {
    String webhookUrl = "http://localhost:8284/webhook";
    String orderId = "order-123";

    CheckoutResponse checkout = new CheckoutResponse();
    checkout.setId("checkout-123");

    UCPCheckoutResponse ucp = new UCPCheckoutResponse();
    ucp.setVersion("2026-01-11");
    checkout.setUcp(ucp);

    OrderConfirmation order = new OrderConfirmation();
    order.setId(orderId);
    checkout.setOrder(order);

    when(objectMapper.writeValueAsString(any())).thenReturn("{}");
    when(extensionsHelper.getFulfillmentResponse(any())).thenReturn(new FulfillmentResponse());

    // Run notify in background as it enters a wait state
    CompletableFuture<Void> future =
        CompletableFuture.runAsync(
            () -> {
              notifier.notify(webhookUrl, checkout);
            });

    // Short sleep to ensure the notifier has sent order_placed and is waiting
    Thread.sleep(200);

    // Trigger the shipping event
    notifier.triggerShipping(orderId);

    // Wait for the async task to complete
    future.get(5, TimeUnit.SECONDS);

    // Verify that restClient.post() was called twice (placed + shipped)
    verify(restClient, times(2)).post();
    verify(objectMapper, atLeastOnce()).writeValueAsString(any());
  }
}
