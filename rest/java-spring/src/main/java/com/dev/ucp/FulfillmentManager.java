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

import com.dev.ucp.entities.AddressEntity;
import com.dev.ucp.entities.PromotionEntity;
import com.dev.ucp.entities.ShippingRateEntity;
import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.dev.ucp.service.shopping.model.FulfillmentAvailableMethodResponse;
import com.dev.ucp.service.shopping.model.FulfillmentDestinationResponse;
import com.dev.ucp.service.shopping.model.FulfillmentGroupResponse;
import com.dev.ucp.service.shopping.model.FulfillmentMethodResponse;
import com.dev.ucp.service.shopping.model.FulfillmentOptionResponse;
import com.dev.ucp.service.shopping.model.FulfillmentResponse;
import com.dev.ucp.service.shopping.model.LineItemResponse;
import com.dev.ucp.service.shopping.model.MessageError;
import com.dev.ucp.service.shopping.model.ShippingDestinationResponse;
import com.dev.ucp.service.shopping.model.TotalResponse;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * Manages fulfillment logic for checkout sessions.
 *
 * <p>Responsible for identifying available shipping destinations, calculating shipping rates, and
 * validating fulfillment selections.
 */
@Component
public class FulfillmentManager {

  @Autowired private AddressEntity.Repository addressRepository;
  @Autowired private ShippingRateEntity.Repository shippingRateRepository;
  @Autowired private PromotionEntity.Repository promotionRepository;
  @Autowired private ExtensionsHelper extensionsHelper;

  public void handleFulfillment(CheckoutResponse checkout, FulfillmentResponse fulfillment) {
    if (fulfillment == null) {
      fulfillment = new FulfillmentResponse();
    }

    addDefaultsAndValidateRequestedFulfillment(checkout, fulfillment);

    FulfillmentMethodResponse fulfillmentMethod = fulfillment.getMethods().get(0);

    long currentGrandTotal =
        checkout.getTotals().stream()
            .filter(total -> total.getType() == TotalResponse.TypeEnum.SUBTOTAL)
            .mapToLong(TotalResponse::getAmount)
            .findFirst()
            .orElse(0L);

    populateMethodDetails(fulfillmentMethod, currentGrandTotal, checkout.getLineItems(), checkout);

    extensionsHelper.setFulfillment(checkout, fulfillment);
  }

  public long recalculateFulfillmentTotals(CheckoutResponse checkout) {
    long fulfillmentTotal = 0;
    FulfillmentResponse fulfillment = extensionsHelper.getFulfillmentResponse(checkout);
    if (fulfillment != null && fulfillment.getMethods() != null) {
      for (FulfillmentMethodResponse fulfillmentMethod : fulfillment.getMethods()) {
        if (fulfillmentMethod.getGroups() != null) {
          for (FulfillmentGroupResponse group : fulfillmentMethod.getGroups()) {
            if (group.getSelectedOptionId() != null
                && group.getSelectedOptionId().isPresent()
                && group.getOptions() != null) {
              String selectedOptionId = group.getSelectedOptionId().get();
              for (FulfillmentOptionResponse option : group.getOptions()) {
                if (option.getId().equals(selectedOptionId) && option.getTotals() != null) {
                  for (TotalResponse total : option.getTotals()) {
                    if (total.getType() == TotalResponse.TypeEnum.TOTAL) {
                      fulfillmentTotal += total.getAmount();
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    return fulfillmentTotal;
  }

  private void addDefaultsAndValidateRequestedFulfillment(
      CheckoutResponse checkout, FulfillmentResponse fulfillment) {
    List<String> allLineItemIds =
        checkout.getLineItems().stream().map(LineItemResponse::getId).collect(Collectors.toList());

    // Initialize available methods
    FulfillmentAvailableMethodResponse availableMethod = new FulfillmentAvailableMethodResponse();
    availableMethod.setType(FulfillmentAvailableMethodResponse.TypeEnum.SHIPPING);
    availableMethod.setLineItemIds(allLineItemIds);
    fulfillment.setAvailableMethods(List.of(availableMethod));

    // Resolve known addresses
    String buyerEmail = (checkout.getBuyer() != null) ? checkout.getBuyer().getEmail() : null;
    List<ShippingDestinationResponse> knownAddresses =
        (buyerEmail != null) ? getKnownAddressesForBuyer(buyerEmail) : new ArrayList<>();

    // Suggested method if none provided
    if (fulfillment.getMethods() == null || fulfillment.getMethods().isEmpty()) {
      FulfillmentMethodResponse defaultMethod = new FulfillmentMethodResponse();
      defaultMethod.setType(FulfillmentMethodResponse.TypeEnum.SHIPPING);
      defaultMethod.setLineItemIds(allLineItemIds);
      fulfillment.setMethods(new ArrayList<>(List.of(defaultMethod)));
    }

    // Merge destinations and assign line items
    for (FulfillmentMethodResponse fulfillmentMethod : fulfillment.getMethods()) {
      // Cast list elements to the interface type for processing
      List<FulfillmentDestinationResponse> requestedDestinations = new ArrayList<>();
      if (fulfillmentMethod.getDestinations() != null) {
        requestedDestinations.addAll(fulfillmentMethod.getDestinations());
      }

      List<FulfillmentDestinationResponse> merged =
          mergeDestinationsPolymorphic(knownAddresses, requestedDestinations);
      fulfillmentMethod.setDestinations(
          merged.stream().map(d -> (ShippingDestinationResponse) d).collect(Collectors.toList()));

      if (fulfillmentMethod.getId() == null) {
        fulfillmentMethod.setId(UUID.randomUUID().toString());
      }

      if (fulfillmentMethod.getDestinations() == null
          || fulfillmentMethod.getDestinations().isEmpty()) {
        checkout.addMessagesItem(
            new MessageError()
                .severity(MessageError.SeverityEnum.RECOVERABLE)
                .type(MessageError.TypeEnum.ERROR)
                .code("no_fulfillment_destinations")
                .path(
                    "$.fulfillment.methods[?(@.id=='"
                        + fulfillmentMethod.getId()
                        + "')].destinations")
                .content("No fulfillment destinations found for the buyer."));
      }

      if (fulfillmentMethod.getGroups() == null || fulfillmentMethod.getGroups().isEmpty()) {
        FulfillmentGroupResponse defaultGroup = new FulfillmentGroupResponse();
        defaultGroup.setLineItemIds(fulfillmentMethod.getLineItemIds());
        fulfillmentMethod.setGroups(new ArrayList<>(List.of(defaultGroup)));
      }

      for (FulfillmentGroupResponse group : fulfillmentMethod.getGroups()) {
        if (group.getId() == null) {
          group.setId(UUID.randomUUID().toString());
        }
      }
    }

    // Validation
    if (fulfillment.getMethods().size() > 1) {
      checkout.addMessagesItem(
          new MessageError()
              .severity(MessageError.SeverityEnum.RECOVERABLE)
              .type(MessageError.TypeEnum.ERROR)
              .code("multiple_fulfillment_methods_not_supported")
              .path("$.fulfillment.methods")
              .content("Multiple fulfillment methods are not supported."));
    } else if (fulfillment.getMethods().get(0).getType()
        != FulfillmentMethodResponse.TypeEnum.SHIPPING) {
      checkout.addMessagesItem(
          new MessageError()
              .severity(MessageError.SeverityEnum.RECOVERABLE)
              .type(MessageError.TypeEnum.ERROR)
              .code("unsupported_fulfillment_method_type")
              .path("$.fulfillment.methods[0]")
              .content("Unsupported fulfillment method type."));
    }
  }

  private List<FulfillmentOptionResponse> getAvailableShippingOptions(
      String countryCode, long subtotal, List<LineItemResponse> lineItems) {
    List<ShippingRateEntity> dbRates =
        shippingRateRepository.findByCountryCodeOrCountryCode("default", countryCode);
    List<FulfillmentOptionResponse> options = new ArrayList<>();

    boolean isFreeShipping = false;
    if (lineItems != null) {
      for (LineItemResponse lineItem : lineItems) {
        if ("bouquet_roses".equals(lineItem.getItem().getId())) {
          isFreeShipping = true;
          break;
        }
      }
    }

    if (!isFreeShipping) {
      List<PromotionEntity> promotions = promotionRepository.findAll();
      for (PromotionEntity promo : promotions) {
        if ("free_shipping".equals(promo.getType()) && subtotal >= promo.getSubtotalThreshold()) {
          isFreeShipping = true;
          break;
        }
      }
    }

    for (ShippingRateEntity rate : dbRates) {
      long price = rate.getPrice();
      String title = rate.getTitle();
      if (isFreeShipping && "standard".equalsIgnoreCase(rate.getServiceLevel())) {
        price = 0;
        title += " (Free)";
      }
      FulfillmentOptionResponse option =
          new FulfillmentOptionResponse().id(rate.getId()).title(title);
      option.addTotalsItem(
          new TotalResponse().type(TotalResponse.TypeEnum.SUBTOTAL).amount(Math.toIntExact(price)));
      option.addTotalsItem(
          new TotalResponse().type(TotalResponse.TypeEnum.TOTAL).amount(Math.toIntExact(price)));
      options.add(option);
    }
    return options;
  }

  private List<ShippingDestinationResponse> getKnownAddressesForBuyer(String email) {
    List<AddressEntity> addressEntities = addressRepository.findByCustomerEmail(email);
    return addressEntities.stream()
        .map(this::convertToShippingDestinationResponse)
        .collect(Collectors.toList());
  }

  private ShippingDestinationResponse convertToShippingDestinationResponse(AddressEntity entity) {
    return new ShippingDestinationResponse()
        .id(entity.getId())
        .streetAddress(entity.getStreetAddress())
        .addressLocality(entity.getCity())
        .addressRegion(entity.getState())
        .postalCode(entity.getPostalCode())
        .addressCountry(entity.getCountry());
  }

  private List<FulfillmentDestinationResponse> mergeDestinationsPolymorphic(
      List<ShippingDestinationResponse> knownAddresses,
      List<FulfillmentDestinationResponse> requested) {
    Map<String, FulfillmentDestinationResponse> merged = new LinkedHashMap<>();
    if (knownAddresses != null) {
      knownAddresses.forEach(k -> merged.put(k.getId(), k));
    }

    if (requested != null) {
      for (FulfillmentDestinationResponse req : requested) {
        String id = FulfillmentUtils.getId(req);
        if (id != null) {
          merged.put(id, req);
          continue;
        }

        // Try to match flat addresses
        if (req instanceof ShippingDestinationResponse sdr) {
          ShippingDestinationResponse matched =
              knownAddresses.stream().filter(k -> isSameAddress(sdr, k)).findFirst().orElse(null);

          if (matched != null) {
            sdr.setId(matched.getId());
          } else {
            sdr.setId(UUID.randomUUID().toString());
          }
          merged.put(sdr.getId(), sdr);
        } else {
          // For other types, generate ID if missing
          // Note: RetailLocationResponse would need cast/set ID if we supported it here
          merged.put(UUID.randomUUID().toString(), req);
        }
      }
    }

    return new ArrayList<>(merged.values());
  }

  private boolean isSameAddress(ShippingDestinationResponse a, ShippingDestinationResponse b) {
    return Objects.equals(a.getStreetAddress(), b.getStreetAddress())
        && Objects.equals(a.getAddressLocality(), b.getAddressLocality())
        && Objects.equals(a.getAddressRegion(), b.getAddressRegion())
        && Objects.equals(a.getPostalCode(), b.getPostalCode())
        && Objects.equals(a.getAddressCountry(), b.getAddressCountry());
  }

  private List<FulfillmentOptionResponse> getOptionsForGroup(
      FulfillmentMethodResponse fulfillmentMethod,
      long currentGrandTotal,
      List<LineItemResponse> lineItems,
      FulfillmentGroupResponse fulfillmentGroup) {

    String selectedId =
        fulfillmentMethod.getSelectedDestinationId() != null
            ? fulfillmentMethod.getSelectedDestinationId().orElse(null)
            : null;

    if (selectedId != null && fulfillmentMethod.getDestinations() != null) {
      return fulfillmentMethod.getDestinations().stream()
          .filter(dest -> FulfillmentUtils.getId(dest).equals(selectedId))
          .findFirst()
          .map(
              dest ->
                  getAvailableShippingOptions(
                      FulfillmentUtils.getCountryCode(dest), currentGrandTotal, lineItems))
          .orElseGet(() -> getAvailableShippingOptions("default", currentGrandTotal, lineItems));
    }

    return getAvailableShippingOptions("default", currentGrandTotal, lineItems);
  }

  private void populateMethodDetails(
      FulfillmentMethodResponse fulfillmentMethod,
      long currentGrandTotal,
      List<LineItemResponse> lineItems,
      CheckoutResponse checkout) {

    for (FulfillmentGroupResponse fulfillmentGroup : fulfillmentMethod.getGroups()) {
      fulfillmentGroup.setOptions(
          getOptionsForGroup(fulfillmentMethod, currentGrandTotal, lineItems, fulfillmentGroup));
    }
  }
}
