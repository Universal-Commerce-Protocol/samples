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

/** Entity representing a customer's address. */
@Entity
@Table(name = "addresses")
public class AddressEntity {

  @org.springframework.stereotype.Repository
  public interface Repository extends JpaRepository<AddressEntity, String> {
    List<AddressEntity> findByCustomerEmail(String customerEmail);
  }

  @Id private String id;
  private String customerEmail;
  private String streetAddress;
  private String city;
  private String state;
  private String postalCode;
  private String country;

  public AddressEntity() {}

  public AddressEntity(
      String id,
      String customerEmail,
      String streetAddress,
      String city,
      String state,
      String postalCode,
      String country) {
    this.id = id;
    this.customerEmail = customerEmail;
    this.streetAddress = streetAddress;
    this.city = city;
    this.state = state;
    this.postalCode = postalCode;
    this.country = country;
  }

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getCustomerEmail() {
    return customerEmail;
  }

  public void setCustomerEmail(String customerEmail) {
    this.customerEmail = customerEmail;
  }

  public String getStreetAddress() {
    return streetAddress;
  }

  public void setStreetAddress(String streetAddress) {
    this.streetAddress = streetAddress;
  }

  public String getCity() {
    return city;
  }

  public void setCity(String city) {
    this.city = city;
  }

  public String getState() {
    return state;
  }

  public void setState(String state) {
    this.state = state;
  }

  public String getPostalCode() {
    return postalCode;
  }

  public void setPostalCode(String postalCode) {
    this.postalCode = postalCode;
  }

  public String getCountry() {
    return country;
  }

  public void setCountry(String country) {
    this.country = country;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    AddressEntity that = (AddressEntity) o;
    return Objects.equals(id, that.id)
        && Objects.equals(customerEmail, that.customerEmail)
        && Objects.equals(streetAddress, that.streetAddress)
        && Objects.equals(city, that.city)
        && Objects.equals(state, that.state)
        && Objects.equals(postalCode, that.postalCode)
        && Objects.equals(country, that.country);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, customerEmail, streetAddress, city, state, postalCode, country);
  }
}