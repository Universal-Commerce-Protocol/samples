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

package com.dev.ucp.actions;

import com.dev.ucp.entities.IdempotencyRecordEntity;
import com.dev.ucp.exceptions.IdempotencyConflictException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Optional;
import java.util.UUID;
import java.util.logging.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

/**
 * Base class for all checkout-related actions, providing common functionality for idempotency
 * handling and request hashing.
 *
 * @param <T> The type of the request payload.
 * @param <R> The type of the response payload.
 */
@Transactional
public abstract class BaseAction<T, R> {

  protected final Logger logger = Logger.getLogger(this.getClass().getName());

  @Autowired protected ObjectMapper objectMapper;

  @Autowired private IdempotencyRecordEntity.Repository idempotencyRecordRepository;

  protected abstract R executeAction(T request);

  public R execute(UUID idempotencyKey, T request) {
    if (idempotencyKey == null) {
      return executeAction(request);
    }
    try {
      String requestPayload = objectMapper.writeValueAsString(request);
      String requestHash = computeHash(requestPayload);

      Optional<IdempotencyRecordEntity> existingRecordOpt =
          idempotencyRecordRepository.findById(idempotencyKey.toString());

      if (existingRecordOpt.isPresent()) {
        IdempotencyRecordEntity existingRecord = existingRecordOpt.get();
        if (!existingRecord.getRequestHash().equals(requestHash)) {
          throw new IdempotencyConflictException(
              "Idempotency key reused with different parameters");
        }
        logger.info(
            String.format(
                "Returning cached response for idempotency key: %s, request hash: %s",
                idempotencyKey.toString(), requestHash));
        return objectMapper.readValue(existingRecord.getResponseBody(), getResponseType());
      }

      R response = executeAction(request);

      String responseBody = objectMapper.writeValueAsString(response);

      saveIdempotencyRecord(idempotencyKey.toString(), requestHash, 201, responseBody);

      return response;
    } catch (JsonProcessingException | NoSuchAlgorithmException e) {
      throw new RuntimeException("Error processing request", e);
    }
  }

  private String computeHash(String data) throws NoSuchAlgorithmException {
    MessageDigest digest = MessageDigest.getInstance("SHA-256");
    byte[] hash = digest.digest(data.getBytes(StandardCharsets.UTF_8));
    StringBuilder hexString = new StringBuilder();
    for (byte b : hash) {
      String hex = Integer.toHexString(0xff & b);
      if (hex.length() == 1) {
        hexString.append('0');
      }
      hexString.append(hex);
    }
    return hexString.toString();
  }

  private void saveIdempotencyRecord(
      String key, String requestHash, int responseStatus, String responseBody) {
    IdempotencyRecordEntity record = new IdempotencyRecordEntity();
    record.setKey(key);
    record.setRequestHash(requestHash);
    record.setResponseStatus(responseStatus);
    record.setResponseBody(responseBody);
    record.setCreatedAt(OffsetDateTime.now().format(DateTimeFormatter.ISO_OFFSET_DATE_TIME));
    idempotencyRecordRepository.save(record);
  }

  protected abstract String getEndpoint();

  protected abstract Class<R> getResponseType();
}
