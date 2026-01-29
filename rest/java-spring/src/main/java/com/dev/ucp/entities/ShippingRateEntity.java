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

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.util.List;
import java.util.Objects;
import org.springframework.data.jpa.repository.JpaRepository;

/** Entity representing a shipping rate for a country and service level. */
@Entity
@Table(name = "shipping_rates")
public class ShippingRateEntity {

  @org.springframework.stereotype.Repository
  public interface Repository extends JpaRepository<ShippingRateEntity, String> {
    List<ShippingRateEntity> findByCountryCodeOrCountryCode(String code1, String code2);
  }

  @Id private String id;
  private String countryCode;
  private String serviceLevel;
  private String title;
  private Integer price;

  public ShippingRateEntity() {}

  public ShippingRateEntity(
      String id, String countryCode, String serviceLevel, String title, Integer price) {
    this.id = id;
    this.countryCode = countryCode;
    this.serviceLevel = serviceLevel;
    this.title = title;
    this.price = price;
  }

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getCountryCode() {
    return countryCode;
  }

  public void setCountryCode(String countryCode) {
    this.countryCode = countryCode;
  }

  public String getServiceLevel() {
    return serviceLevel;
  }

  public void setServiceLevel(String serviceLevel) {
    this.serviceLevel = serviceLevel;
  }

  public String getTitle() {
    return title;
  }

  public void setTitle(String title) {
    this.title = title;
  }

  public Integer getPrice() {
    return price;
  }

  public void setPrice(Integer price) {
    this.price = price;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    ShippingRateEntity that = (ShippingRateEntity) o;
    return Objects.equals(id, that.id)
        && Objects.equals(countryCode, that.countryCode)
        && Objects.equals(serviceLevel, that.serviceLevel)
        && Objects.equals(title, that.title)
        && Objects.equals(price, that.price);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, countryCode, serviceLevel, title, price);
  }
}
