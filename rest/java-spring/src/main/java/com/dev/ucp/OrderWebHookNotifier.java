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

import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.dev.ucp.service.shopping.model.Expectation;
import com.dev.ucp.service.shopping.model.ExpectationLineItemsInner;
import com.dev.ucp.service.shopping.model.FulfillmentEvent;
import com.dev.ucp.service.shopping.model.FulfillmentEventLineItemsInner;
import com.dev.ucp.service.shopping.model.FulfillmentResponse;
import com.dev.ucp.service.shopping.model.OrderEventWebhookRequest;
import com.dev.ucp.service.shopping.model.OrderFulfillment;
import com.dev.ucp.service.shopping.model.OrderLineItem;
import com.dev.ucp.service.shopping.model.OrderLineItemQuantity;
import com.dev.ucp.service.shopping.model.UCPOrderResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.TextNode;
import java.net.URI;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

/**
 * Handles asynchronous webhook notifications for order-related events.
 *
 * <p>This component is responsible for orchestrating the simulated order lifecycle after a checkout
 * is completed. It sends an initial 'order_placed' event and then waits for an external signal (via
 * {@link #triggerShipping(String)}) to send a subsequent 'order_shipped' event.
 *
 * <p>Synchronization between the asynchronous notification thread and the simulation trigger is
 * managed using a {@link ConcurrentHashMap} of {@link CountDownLatch} objects.
 */
@Component
public class OrderWebHookNotifier {
  private static final Logger logger = Logger.getLogger(OrderWebHookNotifier.class.getName());

  private final RestClient restClient;
  @Autowired private ObjectMapper objectMapper;
  @Autowired private ExtensionsHelper extensionsHelper;

  private final Map<String, CountDownLatch> shipmentLatches = new ConcurrentHashMap<>();

  public OrderWebHookNotifier(RestClient.Builder restClientBuilder) {
    this.restClient = restClientBuilder.build();
  }

  /**
   * Initiates the order notification lifecycle for a completed checkout.
   *
   * <p>This method sends an 'order_placed' webhook immediately and then enters a waiting state
   * until a shipping trigger is received or a timeout occurs (60 seconds). Once triggered, it sends
   * an 'order_shipped' webhook with mock tracking details.
   *
   * @param webhookUrl the destination URL for the webhook events.
   * @param checkout the completed checkout session data.
   */
  @Async
  public void notify(String webhookUrl, CheckoutResponse checkout) {
    if (webhookUrl == null || webhookUrl.isEmpty()) {
      logger.warning("No webhook URL provided, skipping notification.");
      return;
    }

    String orderId = checkout.getOrder().getId();
    OrderEventWebhookRequest request = createBaseRequest(checkout);

    // 1. Send order_placed
    request.putAdditionalProperty("event_type", new TextNode("order_placed"));
    sendWebhook(webhookUrl, request);

    // 2. Wait for trigger for order_shipped
    CountDownLatch latch = shipmentLatches.computeIfAbsent(orderId, k -> new CountDownLatch(1));

    try {
      logger.info("Waiting for shipping trigger for order: " + orderId);
      // Wait up to 60 seconds for external trigger
      if (!latch.await(60, TimeUnit.SECONDS)) {
        logger.warning("Timed out waiting for shipping trigger for order: " + orderId);
      }
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      logger.warning("Interrupted while waiting for shipping trigger.");
    } finally {
      shipmentLatches.remove(orderId);
    }

    // 3. Send order_shipped
    request.setEventId(UUID.randomUUID().toString());
    request.setCreatedTime(OffsetDateTime.now());
    request.putAdditionalProperty("event_type", new TextNode("order_shipped"));
    addMockShippingEvent(request);
    sendWebhook(webhookUrl, request);
  }

  /**
   * Signal the notification thread to proceed with sending the 'order_shipped' event.
   *
   * @param orderId the unique identifier of the order to be shipped.
   */
  public void triggerShipping(String orderId) {
    CountDownLatch latch = shipmentLatches.computeIfAbsent(orderId, k -> new CountDownLatch(1));
    logger.info("Triggering shipping for order: " + orderId);
    latch.countDown();
  }

  private void sendWebhook(String url, OrderEventWebhookRequest payload) {
    try {
      String jsonBody = objectMapper.writeValueAsString(payload);
      logger.info("Sending webhook to " + url + " with body: " + jsonBody);
      restClient
          .post()
          .uri(url)
          .contentType(MediaType.APPLICATION_JSON)
          .body(jsonBody)
          .retrieve()
          .toBodilessEntity();
      logger.info("Webhook delivered successfully.");
    } catch (Exception e) {
      logger.severe("Failed to deliver webhook to " + url + ": " + e.getMessage());
    }
  }

  private void addMockShippingEvent(OrderEventWebhookRequest request) {
    if (request.getLineItems() == null) {
      return;
    }

    for (OrderLineItem oli : request.getLineItems()) {
      oli.setStatus(OrderLineItem.StatusEnum.FULFILLED);
      if (oli.getQuantity() != null) {
        oli.getQuantity().setFulfilled(oli.getQuantity().getTotal());
      }
    }

    FulfillmentEvent event = new FulfillmentEvent();
    event.setId(UUID.randomUUID().toString());
    event.setOccurredAt(OffsetDateTime.now());
    event.setType("shipped");
    event.setCarrier("MockCarrier");
    event.setTrackingNumber("MOCK123456789");
    try {
      event.setTrackingUrl(new URI("https://example.com/track/MOCK123456789"));
    } catch (Exception ignored) {}

    List<FulfillmentEventLineItemsInner> fulfillmentLineItems = new ArrayList<>();
    for (OrderLineItem oli : request.getLineItems()) {
      FulfillmentEventLineItemsInner feli = new FulfillmentEventLineItemsInner();
      feli.setId(oli.getId());
      if (oli.getQuantity() != null) {
        feli.setQuantity(oli.getQuantity().getTotal());
      }
      fulfillmentLineItems.add(feli);
    }
    event.setLineItems(fulfillmentLineItems);

    if (request.getFulfillment() == null) {
        request.setFulfillment(new OrderFulfillment());
    }
    request.getFulfillment().addEventsItem(event);
  }

  private OrderEventWebhookRequest createBaseRequest(CheckoutResponse checkout) {
    OrderEventWebhookRequest request = new OrderEventWebhookRequest();

    UCPOrderResponse ucp = new UCPOrderResponse();
    ucp.setVersion(checkout.getUcp().getVersion());
    request.setUcp(ucp);

    request.setId(checkout.getOrder().getId());
    request.setCheckoutId(checkout.getId());
    request.setPermalinkUrl(checkout.getOrder().getPermalinkUrl());

    List<OrderLineItem> orderLineItems = new ArrayList<>();
    if (checkout.getLineItems() != null) {
      for (var li : checkout.getLineItems()) {
        OrderLineItem oli = new OrderLineItem();
        oli.setId(li.getId());
        oli.setItem(li.getItem());

        OrderLineItemQuantity qty = new OrderLineItemQuantity();
        qty.setTotal(li.getQuantity());
        qty.setFulfilled(0);
        oli.setQuantity(qty);

        oli.setStatus(OrderLineItem.StatusEnum.PROCESSING);
        oli.setTotals(li.getTotals());
        orderLineItems.add(oli);
      }
    }
    request.setLineItems(orderLineItems);

    OrderFulfillment fulfillment = new OrderFulfillment();
    FulfillmentResponse checkoutFulfillment = extensionsHelper.getFulfillmentResponse(checkout);
    if (checkoutFulfillment != null && checkoutFulfillment.getMethods() != null) {
      for (var method : checkoutFulfillment.getMethods()) {
        Expectation expectation = new Expectation();
        expectation.setId(UUID.randomUUID().toString());
        expectation.setMethodType(
            Expectation.MethodTypeEnum.fromValue(method.getType().getValue()));

        // Find selected destination
        if (method.getSelectedDestinationId() != null
            && method.getSelectedDestinationId().isPresent()
            && method.getDestinations() != null) {
          String selectedId = method.getSelectedDestinationId().get();
          for (var dest : method.getDestinations()) {
            if (selectedId.equals(FulfillmentUtils.getId(dest))) {
              expectation.setDestination(FulfillmentUtils.getPostalAddress(dest));
              break;
            }
          }
        }
        // Map line items to expectation
        List<ExpectationLineItemsInner> expectationLineItems = new ArrayList<>();
        if (checkout.getLineItems() != null) {
          for (var li : checkout.getLineItems()) {
            ExpectationLineItemsInner eli = new ExpectationLineItemsInner();
            eli.setId(li.getId());
            eli.setQuantity(li.getQuantity());
            expectationLineItems.add(eli);
          }
        }
        expectation.setLineItems(expectationLineItems);
        fulfillment.addExpectationsItem(expectation);
      }
    }
    request.setFulfillment(fulfillment);
    request.setTotals(checkout.getTotals());
    request.setEventId(UUID.randomUUID().toString());
    request.setCreatedTime(OffsetDateTime.now());

    return request;
  }
}
