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

import com.dev.ucp.entities.InventoryEntity;
import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.dev.ucp.service.shopping.model.LineItemResponse;
import com.dev.ucp.service.shopping.model.MessageError;
import java.util.Optional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * Manages all inventory-related operations, including validation and stock reservation. This class
 * is responsible for checking if items are in stock and for reserving them when a checkout is
 * completed.
 */
@Component
public class InventoryManager {

  @Autowired private InventoryEntity.Repository inventoryRepository;

  /**
   * Validates the inventory for all line items in the given checkout response. This method checks
   * for two main conditions: 1. If inventory information is found for the product. 2. If there is
   * sufficient stock for the requested quantity. If any issues are found, appropriate {@link
   * MessageError} objects are added to the checkout's messages list.
   *
   * @param checkout The {@link CheckoutResponse} containing the line items to validate.
   */
  public void validate(CheckoutResponse checkout) {
    if (checkout.getLineItems() == null) {
      return;
    }
    for (LineItemResponse lineItem : checkout.getLineItems()) {
      // It's possible the product wasn't found in a previous step, so the item is null.
      if (lineItem.getItem() == null) {
        continue;
      }
      String productId = lineItem.getItem().getId();
      int requestedQuantity = lineItem.getQuantity();

      Optional<InventoryEntity> inventoryOpt = inventoryRepository.findById(productId);

      if (inventoryOpt.isEmpty()) {
        MessageError error =
            new MessageError()
                .type(MessageError.TypeEnum.ERROR)
                .severity(MessageError.SeverityEnum.RECOVERABLE)
                .code("inventory_not_found")
                .content("Inventory not found for product: " + lineItem.getItem().getTitle())
                .path("$.line_items[?(@.id=='" + lineItem.getId() + "')]");
        checkout.addMessagesItem(error);
        continue;
      }

      InventoryEntity inventory = inventoryOpt.get();
      if (inventory.getQuantity() < requestedQuantity) {
        MessageError error =
            new MessageError()
                .type(MessageError.TypeEnum.ERROR)
                .severity(MessageError.SeverityEnum.RECOVERABLE)
                .code("insufficient_stock")
                .content("Insufficient stock for item " + lineItem.getItem().getTitle())
                .path("$.line_items[?(@.id=='" + lineItem.getId() + "')]");
        checkout.addMessagesItem(error);
      }
    }
  }

  /**
   * Reserves inventory for all line items in the given checkout response. This method decrements
   * the stock quantity for each item in the repository. It assumes that inventory has already been
   * validated prior to this operation. If a product's stock becomes insufficient during the
   * reservation process (which should ideally be prevented by prior validation), an {@link
   * IllegalStateException} is thrown.
   *
   * @param checkout The {@link CheckoutResponse} containing the line items for which to reserve
   *     inventory.
   * @throws IllegalStateException if there is insufficient stock for an item during reservation,
   *     which indicates a logical error if validation was performed correctly.
   */
  public void reserveInventory(CheckoutResponse checkout) {
    for (LineItemResponse lineItem : checkout.getLineItems()) {
      inventoryRepository
          .findById(lineItem.getItem().getId())
          .ifPresent(
              inventoryEntity -> {
                if (inventoryEntity.getQuantity() < lineItem.getQuantity()) {
                  throw new IllegalStateException(
                      "Insufficient stock for item " + lineItem.getItem().getId());
                }
                inventoryEntity.setQuantity(inventoryEntity.getQuantity() - lineItem.getQuantity());
                inventoryRepository.save(inventoryEntity);
              });
    }
  }
}
