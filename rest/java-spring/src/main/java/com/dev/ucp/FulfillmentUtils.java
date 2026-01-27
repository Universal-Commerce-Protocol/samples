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

import com.dev.ucp.service.shopping.model.FulfillmentDestinationRequest;
import com.dev.ucp.service.shopping.model.FulfillmentDestinationResponse;
import com.dev.ucp.service.shopping.model.PostalAddress;
import com.dev.ucp.service.shopping.model.RetailLocationResponse;
import com.dev.ucp.service.shopping.model.ShippingDestinationRequest;
import com.dev.ucp.service.shopping.model.ShippingDestinationResponse;

/**
 * Utility class for handling polymorphic UCP fulfillment destinations.
 *
 * <p>UCP destinations can be either flat shipping addresses or composed retail locations. This
 * utility provides a unified way to extract common data (IDs, addresses, countries) using type
 * discrimination.
 */
public class FulfillmentUtils {

  /**
   * Extracts the unique identifier from a fulfillment destination.
   *
   * @param dest the destination response object.
   * @return the destination ID, or {@code null} if the type is unknown.
   */
  public static String getId(FulfillmentDestinationResponse dest) {
    if (dest instanceof ShippingDestinationResponse sdr) {
      return sdr.getId();
    } else if (dest instanceof RetailLocationResponse rlr) {
      return rlr.getId();
    }
    return null;
  }

  /**
   * Extracts the country code from a fulfillment destination.
   *
   * @param dest the destination response object.
   * @return the ISO country code, or "default" if not specified.
   */
  public static String getCountryCode(FulfillmentDestinationResponse dest) {
    if (dest instanceof ShippingDestinationResponse sdr) {
      return sdr.getAddressCountry() != null ? sdr.getAddressCountry() : "default";
    } else if (dest instanceof RetailLocationResponse rlr && rlr.getAddress() != null) {
      return rlr.getAddress().getAddressCountry() != null
          ? rlr.getAddress().getAddressCountry()
          : "default";
    }
    return "default";
  }

  /**
   * Extracts or constructs a {@link PostalAddress} from a fulfillment destination.
   *
   * @param dest the destination response object.
   * @return a {@link PostalAddress} representation, or {@code null} if not applicable.
   */
  public static PostalAddress getPostalAddress(FulfillmentDestinationResponse dest) {
    if (dest instanceof RetailLocationResponse rlr) {
      return rlr.getAddress();
    } else if (dest instanceof ShippingDestinationResponse sdr) {
      PostalAddress pa = new PostalAddress();
      pa.setStreetAddress(sdr.getStreetAddress());
      pa.setExtendedAddress(sdr.getExtendedAddress());
      pa.setAddressLocality(sdr.getAddressLocality());
      pa.setAddressRegion(sdr.getAddressRegion());
      pa.setAddressCountry(sdr.getAddressCountry());
      pa.setPostalCode(sdr.getPostalCode());
      pa.setFirstName(sdr.getFirstName());
      pa.setLastName(sdr.getLastName());
      pa.setFullName(sdr.getFullName());
      pa.setPhoneNumber(sdr.getPhoneNumber());
      return pa;
    }
    return null;
  }

  /**
   * Extracts the unique identifier from a fulfillment destination request.
   *
   * @param dest the destination request object.
   * @return the destination ID, or {@code null} if not provided.
   */
  public static String getId(FulfillmentDestinationRequest dest) {
    if (dest instanceof ShippingDestinationRequest sdr) {
      return sdr.getId();
    }
    // RetailLocationRequest usually does not have an ID on create/update,
    // it's selected via name or external reference in the spec.
    return null;
  }
}
