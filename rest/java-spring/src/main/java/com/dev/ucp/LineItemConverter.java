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

import com.dev.ucp.entities.ProductEntity;
import com.dev.ucp.exceptions.InvalidRequestException;
import com.dev.ucp.service.shopping.model.ItemCreateRequest;
import com.dev.ucp.service.shopping.model.ItemResponse;
import com.dev.ucp.service.shopping.model.ItemUpdateRequest;
import com.dev.ucp.service.shopping.model.LineItemCreateRequest;
import com.dev.ucp.service.shopping.model.LineItemResponse;
import com.dev.ucp.service.shopping.model.LineItemUpdateRequest;
import com.dev.ucp.service.shopping.model.TotalResponse;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * A converter class responsible for transforming LineItem request objects into LineItemResponse
 * objects. This includes fetching authoritative product data from the database to populate fields
 * like price and title.
 */
@Component
public class LineItemConverter {

  @Autowired private ProductEntity.Repository productRepository;

  /**
   * Converts a list of {@link LineItemCreateRequest} objects into a list of {@link
   * LineItemResponse} objects, ensuring that a new unique ID is generated for each line item.
   *
   * <p>This method processes each line item individually, converting its associated item data by
   * fetching authoritative product information.
   *
   * @param lineItems The list of {@link LineItemCreateRequest} objects to convert.
   * @return A list of fully populated {@link LineItemResponse} objects.
   */
  public List<LineItemResponse> convertFromCreateRequest(List<LineItemCreateRequest> lineItems) {
    return convertLineItems(
        lineItems,
        r -> null, // Always generate a new ID for create requests
        LineItemCreateRequest::getQuantity,
        LineItemCreateRequest::getItem,
        ItemCreateRequest::getId);
  }

  /**
   * Converts a list of {@link LineItemUpdateRequest} objects into a list of {@link
   * LineItemResponse} objects, preserving the existing line item ID if provided.
   *
   * @param lineItems The list of {@link LineItemUpdateRequest} objects to convert.
   * @return A list of fully populated {@link LineItemResponse} objects.
   */
  public List<LineItemResponse> convertFromUpdateRequest(List<LineItemUpdateRequest> lineItems) {
    return convertLineItems(
        lineItems,
        LineItemUpdateRequest::getId, // Use existing ID if present
        LineItemUpdateRequest::getQuantity,
        LineItemUpdateRequest::getItem,
        ItemUpdateRequest::getId);
  }

  /**
   * Converts a list of generic line item request objects into a list of {@link LineItemResponse}
   * objects. This method processes each line item individually, converting its associated item data
   * by fetching authoritative product information.
   *
   * @param lineItems The list of generic line item request objects.
   * @param lineItemIdExtractor A function to extract the line item ID from the request object.
   * @param quantityExtractor A function to extract the quantity from the request object.
   * @param itemExtractor A function to extract the item request object from the line item request.
   * @param itemIdExtractor A function to extract the item ID from the item request object.
   * @param <LI> The type of the line item request object.
   * @param <I> The type of the item request object within the line item request.
   * @return A list of {@link LineItemResponse} objects, fully populated with product details.
   * @throws RuntimeException if a {@link URISyntaxException} occurs during item conversion
   *     (internal error).
   */
  private <LI, I> List<LineItemResponse> convertLineItems(
      List<LI> lineItems,
      Function<LI, String> lineItemIdExtractor,
      Function<LI, Integer> quantityExtractor,
      Function<LI, I> itemExtractor,
      Function<I, String> itemIdExtractor) {
    if (lineItems == null) {
      return new ArrayList<>();
    }
    return lineItems.stream()
        .map(
            item -> {
              try {
                return convertLineItem(
                    item, lineItemIdExtractor, quantityExtractor, itemExtractor, itemIdExtractor);
              } catch (URISyntaxException e) {
                // This is an internal error, so we can still throw a runtime exception
                throw new RuntimeException("Error converting line item", e);
              }
            })
        .collect(Collectors.toList());
  }

  /**
   * Converts a generic line item request object into a {@link LineItemResponse} object. It extracts
   * details from the request and populates the response, including fetching authoritative product
   * details for the associated item.
   *
   * @param req The generic line item request object.
   * @param lineItemIdExtractor A function to extract the line item ID from the request object.
   * @param quantityExtractor A function to extract the quantity from the request object.
   * @param itemExtractor A function to extract the item request object from the line item request.
   * @param itemIdExtractor A function to extract the item ID from the item request object.
   * @param <LI> The type of the line item request object.
   * @param <I> The type of the item request object within the line item request.
   * @return A {@link LineItemResponse} object, populated with details from the request and product
   *     data.
   * @throws URISyntaxException if a URI for the item image is invalid.
   * @throws InvalidRequestException if the product associated with the item ID is not found.
   */
  private <LI, I> LineItemResponse convertLineItem(
      LI req,
      Function<LI, String> lineItemIdExtractor,
      Function<LI, Integer> quantityExtractor,
      Function<LI, I> itemExtractor,
      Function<I, String> itemIdExtractor)
      throws URISyntaxException {
    LineItemResponse resp = new LineItemResponse();
    String lineItemId = lineItemIdExtractor.apply(req);
    if (lineItemId == null) {
      lineItemId = UUID.randomUUID().toString();
    }
    resp.setId(lineItemId);
    resp.setQuantity(quantityExtractor.apply(req));
    I item = itemExtractor.apply(req);
    String itemId = itemIdExtractor.apply(item);

    Optional<ProductEntity> productOpt = productRepository.findById(itemId);
    if (productOpt.isEmpty()) {
      // TODO: This should be a MessageError instead. But current spec marks the title and price as
      // required, so we have to throw an exception.
      throw new InvalidRequestException("Product not found: " + itemId);
    }
    ProductEntity product = productOpt.get();

    ItemResponse itemResponse = new ItemResponse();
    itemResponse.setId(product.getId());
    itemResponse.setTitle(product.getTitle());
    itemResponse.setPrice(product.getPrice());
    itemResponse.setImageUrl(new URI("https://example.com/image.png")); // Dummy image URL
    resp.setItem(itemResponse);

    long baseAmount = (long) itemResponse.getPrice() * resp.getQuantity();
    List<TotalResponse> totals = new ArrayList<>();
    totals.add(
        new TotalResponse()
            .type(TotalResponse.TypeEnum.SUBTOTAL)
            .amount(Math.toIntExact(baseAmount)));
    totals.add(
        new TotalResponse().type(TotalResponse.TypeEnum.TOTAL).amount(Math.toIntExact(baseAmount)));
    resp.setTotals(totals);

    return resp;
  }
}
