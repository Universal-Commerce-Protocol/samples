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

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.when;

import com.dev.ucp.entities.ProductEntity;
import com.dev.ucp.exceptions.InvalidRequestException;
import com.dev.ucp.service.shopping.model.ItemCreateRequest;
import com.dev.ucp.service.shopping.model.ItemUpdateRequest;
import com.dev.ucp.service.shopping.model.LineItemCreateRequest;
import com.dev.ucp.service.shopping.model.LineItemResponse;
import com.dev.ucp.service.shopping.model.LineItemUpdateRequest;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;

@SpringBootTest
public class LineItemConverterTest {

  @Autowired private LineItemConverter lineItemConverter;

  @MockBean private ProductEntity.Repository productRepository;

  private LineItemCreateRequest createLineItemCreateRequest(String productId, int quantity) {
    LineItemCreateRequest requestItem = new LineItemCreateRequest();
    requestItem.setItem(new ItemCreateRequest().id(productId));
    requestItem.setQuantity(quantity);
    return requestItem;
  }

  private LineItemUpdateRequest createLineItemUpdateRequest(
      String lineItemId, String productId, int quantity) {
    LineItemUpdateRequest requestItem = new LineItemUpdateRequest();
    requestItem.setId(lineItemId);
    requestItem.setItem(new ItemUpdateRequest().id(productId));
    requestItem.setQuantity(quantity);
    return requestItem;
  }

  @Test
  void convertFromCreateRequest_shouldConvertSuccessfully() {
    ProductEntity product = new ProductEntity("prod-1", "Product 1", 1000);
    when(productRepository.findById("prod-1")).thenReturn(Optional.of(product));

    List<LineItemCreateRequest> requestItems = new ArrayList<>();
    requestItems.add(createLineItemCreateRequest("prod-1", 2));

    List<LineItemResponse> responseItems = lineItemConverter.convertFromCreateRequest(requestItems);

    assertEquals(1, responseItems.size());
    LineItemResponse responseItem = responseItems.get(0);
    assertNotNull(responseItem.getItem());

    assertAll(
        "Line Item Conversion from Create Request",
        () -> assertNotNull(responseItem.getId()),
        () -> assertEquals("prod-1", responseItem.getItem().getId()),
        () -> assertEquals("Product 1", responseItem.getItem().getTitle()),
        () -> assertEquals(1000, responseItem.getItem().getPrice()),
        () -> assertEquals(2, responseItem.getQuantity()),
        () -> assertNotNull(responseItem.getTotals()),
        () -> assertEquals(2, responseItem.getTotals().size()),
        () -> assertEquals(2000, responseItem.getTotals().get(0).getAmount()),
        () -> assertEquals(2000, responseItem.getTotals().get(1).getAmount()));
  }

  @Test
  void convertFromCreateRequest_shouldThrowException_whenProductNotFound() {
    when(productRepository.findById("prod-1")).thenReturn(Optional.empty());

    List<LineItemCreateRequest> requestItems = new ArrayList<>();
    requestItems.add(createLineItemCreateRequest("prod-1", 2));

    InvalidRequestException exception =
        assertThrows(
            InvalidRequestException.class,
            () -> lineItemConverter.convertFromCreateRequest(requestItems));

    assertEquals("Product not found: prod-1", exception.getMessage());
  }

  @Test
  void convertFromUpdateRequest_shouldPreserveExistingId() {
    ProductEntity product = new ProductEntity("prod-1", "Product 1", 1000);
    when(productRepository.findById("prod-1")).thenReturn(Optional.of(product));

    String existingId = UUID.randomUUID().toString();
    List<LineItemUpdateRequest> requestItems = new ArrayList<>();
    requestItems.add(createLineItemUpdateRequest(existingId, "prod-1", 2));

    List<LineItemResponse> responseItems = lineItemConverter.convertFromUpdateRequest(requestItems);

    assertEquals(1, responseItems.size());
    assertEquals(existingId, responseItems.get(0).getId());
  }

  @Test
  void convertFromUpdateRequest_shouldGenerateNewId_whenIdNotProvided() {
    ProductEntity product = new ProductEntity("prod-1", "Product 1", 1000);
    when(productRepository.findById("prod-1")).thenReturn(Optional.of(product));

    List<LineItemUpdateRequest> requestItems = new ArrayList<>();
    requestItems.add(createLineItemUpdateRequest(null, "prod-1", 2));

    List<LineItemResponse> responseItems = lineItemConverter.convertFromUpdateRequest(requestItems);

    assertEquals(1, responseItems.size());
    assertNotNull(responseItems.get(0).getId());
  }
}
