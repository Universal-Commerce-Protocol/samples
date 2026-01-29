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
import java.util.Objects;
import org.springframework.data.jpa.repository.JpaRepository;

/** Entity representing a shop promotion. */
@Entity
@Table(name = "promotions")
public class PromotionEntity {

  @org.springframework.stereotype.Repository
  public interface Repository extends JpaRepository<PromotionEntity, String> {}

  @Id private String id;
  private String title;
  private String type;
  private Integer subtotalThreshold;

  public PromotionEntity() {}

  public PromotionEntity(String id, String title, String type, Integer subtotalThreshold) {
    this.id = id;
    this.title = title;
    this.type = type;
    this.subtotalThreshold = subtotalThreshold;
  }

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getTitle() {
    return title;
  }

  public void setTitle(String title) {
    this.title = title;
  }

  public String getType() {
    return type;
  }

  public void setType(String type) {
    this.type = type;
  }

  public Integer getSubtotalThreshold() {
    return subtotalThreshold;
  }

  public void setSubtotalThreshold(Integer subtotalThreshold) {
    this.subtotalThreshold = subtotalThreshold;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    PromotionEntity that = (PromotionEntity) o;
    return Objects.equals(id, that.id)
        && Objects.equals(title, that.title)
        && Objects.equals(type, that.type)
        && Objects.equals(subtotalThreshold, that.subtotalThreshold);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, title, type, subtotalThreshold);
  }
}