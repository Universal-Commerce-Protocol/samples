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
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.when;

import com.dev.ucp.entities.InventoryEntity;
import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.dev.ucp.service.shopping.model.ItemResponse;
import com.dev.ucp.service.shopping.model.LineItemResponse;
import com.dev.ucp.service.shopping.model.MessageError;
import java.util.ArrayList;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;

@SpringBootTest
public class InventoryManagerTest {

  @Autowired private InventoryManager inventoryManager;

  @MockBean private InventoryEntity.Repository inventoryRepository;

  private CheckoutResponse checkout;

  @BeforeEach
  void setUp() {
    checkout = new CheckoutResponse();
    checkout.setLineItems(new ArrayList<>());
  }

  private LineItemResponse createLineItem(String productId, String title, int quantity) {
    LineItemResponse lineItem = new LineItemResponse();
    lineItem.setId(productId); // We can use the product ID as the line item ID for testing.
    lineItem.setItem(new ItemResponse().id(productId).title(title));
    lineItem.setQuantity(quantity);
    return lineItem;
  }

  @Test
  void validate_shouldAddMessage_whenInventoryNotFound() {
    checkout.getLineItems().add(createLineItem("prod-1", "Product 1", 2));
    when(inventoryRepository.findById("prod-1")).thenReturn(Optional.empty());

    inventoryManager.validate(checkout);

    assertEquals(1, checkout.getMessages().size());
    MessageError error = (MessageError) checkout.getMessages().get(0);
    assertAll(
        "Inventory Not Found Error",
        () -> assertEquals("$.line_items[?(@.id=='prod-1')]", error.getPath()));
  }

  @Test
  void validate_shouldAddMessage_whenInsufficientStock() {
    checkout.getLineItems().add(createLineItem("prod-1", "Product 1", 5));
    when(inventoryRepository.findById("prod-1"))
        .thenReturn(Optional.of(new InventoryEntity("prod-1", 2)));

    inventoryManager.validate(checkout);

    assertEquals(1, checkout.getMessages().size());
    MessageError error = (MessageError) checkout.getMessages().get(0);
    assertAll(
        "Insufficient Stock Error",
        () -> assertEquals("insufficient_stock", error.getCode()),
        () -> assertEquals("$.line_items[?(@.id=='prod-1')]", error.getPath()));
  }

  @Test
  void validate_shouldPass_whenStockIsSufficient() {
    checkout.getLineItems().add(createLineItem("prod-1", "Product 1", 2));
    when(inventoryRepository.findById("prod-1"))
        .thenReturn(Optional.of(new InventoryEntity("prod-1", 10)));

    inventoryManager.validate(checkout);

    assertTrue(checkout.getMessages() == null || checkout.getMessages().isEmpty());
  }

  @Test
  void reserveInventory_shouldThrowException_whenInsufficientStock() {
    checkout.getLineItems().add(createLineItem("prod-1", "Product 1", 5));

    when(inventoryRepository.findById("prod-1"))
        .thenReturn(Optional.of(new InventoryEntity("prod-1", 2)));

    assertThrows(IllegalStateException.class, () -> inventoryManager.reserveInventory(checkout));
  }

  @Test
  void reserveInventory_shouldUpdateStock_whenSufficientStock() {
    InventoryEntity initialInventory = new InventoryEntity("prod-1", 10);
    checkout.getLineItems().add(createLineItem("prod-1", "Product 1", 2));

    when(inventoryRepository.findById("prod-1")).thenReturn(Optional.of(initialInventory));
    inventoryManager.reserveInventory(checkout);

    assertEquals(8, initialInventory.getQuantity()); // Verify stock is decremented to 8.
  }
}
