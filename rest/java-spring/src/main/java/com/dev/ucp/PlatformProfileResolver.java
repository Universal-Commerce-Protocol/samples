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

import com.fasterxml.jackson.databind.JsonNode;
import java.util.Optional;
import java.util.logging.Logger;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

/**
 * Utility for resolving platform UCP profiles.
 *
 * <p>Retrieves the discovery profile from the platform to determine capability endpoints and
 * configuration.
 */
@Component
public class PlatformProfileResolver {
  private static final Logger logger = Logger.getLogger(PlatformProfileResolver.class.getName());
  private final RestClient restClient;

  public PlatformProfileResolver(RestClient.Builder restClientBuilder) {
    this.restClient = restClientBuilder.build();
  }

  /**
   * Fetches the platform's UCP profile and extracts the webhook URL for the order capability.
   *
   * @param profileUri The URI of the platform's profile.
   * @return An Optional containing the webhook URL if found.
   */
  public Optional<String> resolveWebhookUrl(String profileUri) {
    if (profileUri == null || profileUri.isEmpty()) {
      return Optional.empty();
    }

    try {
      logger.info("Fetching platform profile from: " + profileUri);
      JsonNode profile = restClient.get().uri(profileUri).retrieve().body(JsonNode.class);

      if (profile == null) {
        return Optional.empty();
      }

      JsonNode capabilities = profile.at("/ucp/capabilities");
      if (capabilities.isArray()) {
        for (JsonNode cap : capabilities) {
          if ("dev.ucp.shopping.order".equals(cap.path("name").asText())) {
            String url = cap.at("/config/webhook_url").asText();
            if (url != null && !url.isEmpty()) {
              logger.info("Resolved webhook URL: " + url);
              return Optional.of(url);
            }
          }
        }
      }
    } catch (Exception e) {
      logger.warning(
          "Failed to resolve platform profile from " + profileUri + ": " + e.getMessage());
    }
    return Optional.empty();
  }
}
