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

package com.dev.ucp.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Controller for the UCP discovery endpoint.
 *
 * <p>Serves the discovery profile which describes the capabilities and service endpoints of this
 * UCP implementation.
 */
@RestController
public class DiscoveryController {

  private static final String SHOP_ID = UUID.randomUUID().toString();

  @Value("${server.port:8080}")
  private int port;

  @Autowired private ResourceLoader resourceLoader;

  @Autowired private ObjectMapper objectMapper;

  @GetMapping("/.well-known/ucp")
  public Object getDiscoveryProfile() throws IOException {
    Resource resource = resourceLoader.getResource("classpath:discovery_profile.json");
    try (InputStream inputStream = resource.getInputStream()) {
      String template = new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
      // For simplicity, we'll replace the endpoint with a placeholder.
      // A more robust solution would dynamically determine the endpoint URL.
      String profileJson =
          template
              .replace("{{ENDPOINT}}", "http://localhost:" + port + "/ucp")
              .replace("{{SHOP_ID}}", SHOP_ID);
      return objectMapper.readValue(profileJson, Object.class);
    }
  }
}
