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

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

import com.dev.ucp.entities.AddressEntity;
import com.dev.ucp.entities.PromotionEntity;
import com.dev.ucp.entities.ShippingRateEntity;
import com.dev.ucp.service.shopping.model.*;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.openapitools.jackson.nullable.JsonNullable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;

@SpringBootTest
public class FulfillmentManagerTest {

  @Autowired private FulfillmentManager fulfillmentManager;
  @Autowired private ExtensionsHelper extensionsHelper;

  @MockBean private AddressEntity.Repository addressRepository;
  @MockBean private ShippingRateEntity.Repository shippingRateRepository;
  @MockBean private PromotionEntity.Repository promotionRepository;

  private CheckoutResponse checkout;
  private final String buyerEmail = "test@example.com";

  @BeforeEach
  void setUp() {
    checkout = new CheckoutResponse();
    checkout.setBuyer(new Buyer().email(buyerEmail));
    checkout.setLineItems(new ArrayList<>());
    checkout.addLineItemsItem(
        new LineItemResponse()
            .id("li_1")
            .item(new ItemResponse().id("item_1").price(1000).title("Item 1"))
            .quantity(1));
    checkout.setTotals(new ArrayList<>());
    checkout.addTotalsItem(new TotalResponse().type(TotalResponse.TypeEnum.SUBTOTAL).amount(1000));

    when(promotionRepository.findAll()).thenReturn(Collections.emptyList());
    when(shippingRateRepository.findByCountryCodeOrCountryCode(anyString(), anyString()))
        .thenReturn(Collections.emptyList());
  }

  @Test
  void handleFulfillment_shouldProposeDefaultShipping_whenNoFulfillmentProvided() {
    when(addressRepository.findByCustomerEmail(buyerEmail)).thenReturn(Collections.emptyList());
    when(shippingRateRepository.findByCountryCodeOrCountryCode("default", "default"))
        .thenReturn(
            List.of(
                new ShippingRateEntity(
                    "std-ship", "default", "standard", "Standard Shipping", 500)));

    fulfillmentManager.handleFulfillment(checkout, null);

    FulfillmentResponse fr = extensionsHelper.getFulfillmentResponse(checkout);
    assertNotNull(fr);
    assertEquals(1, fr.getMethods().size());
    FulfillmentMethodResponse method = fr.getMethods().get(0);
    assertEquals(FulfillmentMethodResponse.TypeEnum.SHIPPING, method.getType());
    assertTrue(method.getDestinations().isEmpty());
    assertEquals(1, method.getGroups().size());
    assertEquals(1, method.getGroups().get(0).getOptions().size());
    assertEquals("std-ship", method.getGroups().get(0).getOptions().get(0).getId());
  }

  @Test
  void handleFulfillment_shouldMergeRequestedDestinationsWithKnownAddresses() {
    AddressEntity knownAddr =
        new AddressEntity("addr_1", buyerEmail, "123 Main St", "Springfield", "IL", "62704", "US");
    when(addressRepository.findByCustomerEmail(buyerEmail)).thenReturn(List.of(knownAddr));

    FulfillmentResponse requested = new FulfillmentResponse();
    FulfillmentMethodResponse requestedMethod = new FulfillmentMethodResponse();
    requestedMethod.setType(FulfillmentMethodResponse.TypeEnum.SHIPPING);
    ShippingDestinationResponse newDest =
        new ShippingDestinationResponse()
            .id("dest_new")
            .streetAddress("456 New St")
            .addressCountry("US")
            .postalCode("12345");
    requestedMethod.addDestinationsItem(newDest);
    requested.addMethodsItem(requestedMethod);

    fulfillmentManager.handleFulfillment(checkout, requested);

    FulfillmentResponse fr = extensionsHelper.getFulfillmentResponse(checkout);
    FulfillmentMethodResponse method = fr.getMethods().get(0);
    assertEquals(2, method.getDestinations().size());
    assertTrue(
        method.getDestinations().stream()
            .anyMatch(d -> "addr_1".equals(FulfillmentUtils.getId(d))));
    assertTrue(
        method.getDestinations().stream()
            .anyMatch(d -> "dest_new".equals(FulfillmentUtils.getId(d))));
  }

  @Test
  void handleFulfillment_shouldAddError_whenNoDestinationsFound() {
    when(addressRepository.findByCustomerEmail(buyerEmail)).thenReturn(Collections.emptyList());

    fulfillmentManager.handleFulfillment(checkout, null);

    assertTrue(
        checkout.getMessages().stream()
            .anyMatch(
                m ->
                    m instanceof MessageError
                        && "no_fulfillment_destinations".equals(((MessageError) m).getCode())));
  }

  @Test
  void handleFulfillment_shouldAddError_whenMultipleMethodsRequested() {
    FulfillmentResponse requested = new FulfillmentResponse();
    requested.addMethodsItem(
        new FulfillmentMethodResponse().type(FulfillmentMethodResponse.TypeEnum.SHIPPING));
    requested.addMethodsItem(
        new FulfillmentMethodResponse().type(FulfillmentMethodResponse.TypeEnum.PICKUP));

    fulfillmentManager.handleFulfillment(checkout, requested);

    assertTrue(
        checkout.getMessages().stream()
            .anyMatch(
                m ->
                    m instanceof MessageError
                        && "multiple_fulfillment_methods_not_supported"
                            .equals(((MessageError) m).getCode())));
  }

  @Test
  void handleFulfillment_shouldApplyFreeShipping_whenThresholdMet() {
    PromotionEntity freeShippingPromo =
        new PromotionEntity("promo_1", "Free Shipping", "free_shipping", 500);
    when(promotionRepository.findAll()).thenReturn(List.of(freeShippingPromo));
    when(shippingRateRepository.findByCountryCodeOrCountryCode("default", "default"))
        .thenReturn(
            List.of(
                new ShippingRateEntity(
                    "std-ship", "default", "standard", "Standard Shipping", 500)));

    // checkout subtotal is 1000, which is > 500 threshold
    fulfillmentManager.handleFulfillment(checkout, null);

    FulfillmentResponse fr = extensionsHelper.getFulfillmentResponse(checkout);
    FulfillmentOptionResponse option =
        fr.getMethods().get(0).getGroups().get(0).getOptions().get(0);
    assertEquals(0, option.getTotals().get(0).getAmount());
    assertTrue(option.getTitle().contains("(Free)"));
  }

  @Test
  void recalculateFulfillmentTotals_shouldSumTotalOfSelectedOptions() {
    FulfillmentResponse fr = new FulfillmentResponse();
    FulfillmentMethodResponse method = new FulfillmentMethodResponse();
    method.setType(FulfillmentMethodResponse.TypeEnum.SHIPPING);
    FulfillmentGroupResponse group = new FulfillmentGroupResponse();
    group.setSelectedOptionId(JsonNullable.of("opt_1"));
    FulfillmentOptionResponse option = new FulfillmentOptionResponse().id("opt_1").title("Option 1");
    option.addTotalsItem(new TotalResponse().type(TotalResponse.TypeEnum.TOTAL).amount(750));
    group.addOptionsItem(option);
    method.addGroupsItem(group);
    fr.addMethodsItem(method);

    extensionsHelper.setFulfillment(checkout, fr);

    long total = fulfillmentManager.recalculateFulfillmentTotals(checkout);
    assertEquals(750, total);
  }
}
