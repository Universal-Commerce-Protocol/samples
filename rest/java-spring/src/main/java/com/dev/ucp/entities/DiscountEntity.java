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

package com.dev.ucp.entities;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.util.Objects;
import org.springframework.data.jpa.repository.JpaRepository;

/** Entity representing a discount code. */
@Entity
@Table(name = "discounts")
public class DiscountEntity {

  @org.springframework.stereotype.Repository
  public interface Repository extends JpaRepository<DiscountEntity, String> {}

  @Id private String code;
  private String description;
  private String type;

  @Column(name = "discount_value")
  private Integer discountValue;

  public DiscountEntity() {}

  public DiscountEntity(String code, String description, String type, Integer value) {
    this.code = code;
    this.description = description;
    this.type = type;
    this.discountValue = value;
  }

  public String getCode() {
    return code;
  }

  public void setCode(String code) {
    this.code = code;
  }

  public String getDescription() {
    return description;
  }

  public void setDescription(String description) {
    this.description = description;
  }

  public String getType() {
    return type;
  }

  public void setType(String type) {
    this.type = type;
  }

  public Integer getValue() {
    return discountValue;
  }

  public void setValue(Integer value) {
    this.discountValue = value;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    DiscountEntity that = (DiscountEntity) o;
    return Objects.equals(code, that.code)
        && Objects.equals(description, that.description)
        && Objects.equals(type, that.type)
        && Objects.equals(discountValue, that.discountValue);
  }

  @Override
  public int hashCode() {
    return Objects.hash(code, description, type, discountValue);
  }
}