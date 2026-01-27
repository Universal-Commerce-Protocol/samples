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

package com.dev.ucp.service.shopping;

import com.dev.ucp.PlatformProfileResolver;
import com.dev.ucp.actions.CancelCheckoutAction;
import com.dev.ucp.actions.CompleteCheckoutAction;
import com.dev.ucp.actions.CreateCheckoutAction;
import com.dev.ucp.actions.GetCheckoutAction;
import com.dev.ucp.actions.UpdateCheckoutAction;
import com.dev.ucp.service.shopping.model.CheckoutCreateRequest;
import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.dev.ucp.service.shopping.model.CheckoutUpdateRequest;
import com.dev.ucp.service.shopping.model.CompleteCheckoutRequest;
import java.util.UUID;
import javax.annotation.Generated;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.context.request.NativeWebRequest;

/**
 * Implementation of the UCP Shopping API for managing checkout sessions.
 *
 * <p>Delegates business logic to specialized Action classes.
 */
@Generated(
    value = "org.openapitools.codegen.languages.SpringCodegen",
    date = "2025-12-22T13:22:18.790633199Z[Etc/UTC]",
    comments = "Generator version: 7.17.0")
@Controller
@RequestMapping("${openapi.uCPShoppingService.base-path:/ucp}")
public class CheckoutSessionsApiController implements CheckoutSessionsApi {

  private static final Logger logger = LoggerFactory.getLogger(CheckoutSessionsApiController.class);

  private final NativeWebRequest request;

  private final CreateCheckoutAction createCheckoutAction;

  private final PlatformProfileResolver platformProfileResolver;

  private final GetCheckoutAction getCheckoutAction;

  private final UpdateCheckoutAction updateCheckoutAction;

  private final CancelCheckoutAction cancelCheckoutAction;

  private final CompleteCheckoutAction completeCheckoutAction;

  private final boolean failOnNullVersion;

  private static class UcpAgentInfo {
    String version;
    String profile;
  }

  @Autowired
  public CheckoutSessionsApiController(
      NativeWebRequest request,
      CreateCheckoutAction createCheckoutAction,
      GetCheckoutAction getCheckoutAction,
      UpdateCheckoutAction updateCheckoutAction,
      CancelCheckoutAction cancelCheckoutAction,
      CompleteCheckoutAction completeCheckoutAction,
      PlatformProfileResolver platformProfileResolver,
      @Value("${dev.ucp.version_check.fail_on_null:true}") boolean failOnNullVersion) {
    this.request = request;
    this.createCheckoutAction = createCheckoutAction;
    this.getCheckoutAction = getCheckoutAction;
    this.updateCheckoutAction = updateCheckoutAction;
    this.cancelCheckoutAction = cancelCheckoutAction;
    this.completeCheckoutAction = completeCheckoutAction;
    this.platformProfileResolver = platformProfileResolver;
    this.failOnNullVersion = failOnNullVersion;
  }

  private UcpAgentInfo parseAndValidateUcpAgentHeader(String ucPAgent) {
    logger.info("UCP-Agent header: {}", ucPAgent);
    if (ucPAgent == null) {
      throw new IllegalArgumentException("UCP-Agent header is missing.");
    }
    UcpAgentInfo info = new UcpAgentInfo();
    for (String part : ucPAgent.split(";")) {
      String[] kv = part.trim().split("=", 2);
      if (kv.length == 2) {
        String key = kv[0].trim();
        String val = kv[1].trim();
        if (val.length() > 1 && val.startsWith("\"") && val.endsWith("\"")) {
          val = val.substring(1, val.length() - 1);
        }
        if ("version".equals(key)) {
          info.version = val;
        } else if ("profile".equals(key)) {
          info.profile = val;
        }
      }
    }

    String expectedVersion = "2026-01-11";
    if (!expectedVersion.equals(info.version)) {
      // TODO: remove this once coformance tests are updated.
      if (info.version == null && !failOnNullVersion) {
        logger.warn(
            "UCP-Agent header has missing 'version'. Continuing as"
                + " dev.ucp.version_check.fail_on_null is false.");
      } else {
        logger.error(
            "UCP-Agent header has invalid or missing 'version'. Expected {}. Found {}.",
            expectedVersion,
            info.version);
        throw new IllegalArgumentException(
            "UCP-Agent header has invalid or missing 'version'. Expected '2026-01-11'.");
      }
    }
    return info;
  }

  @Override
  public ResponseEntity<CheckoutResponse> createCheckout(
      String requestSignature,
      UUID idempotencyKey,
      UUID requestId,
      String ucPAgent,
      CheckoutCreateRequest checkoutCreateRequest,
      String authorization,
      String xAPIKey,
      String userAgent,
      String contentType,
      String accept,
      String acceptLanguage,
      String acceptEncoding) {
    parseAndValidateUcpAgentHeader(ucPAgent);
    return ResponseEntity.status(HttpStatus.CREATED)
        .body(createCheckoutAction.createCheckoutSession(idempotencyKey, checkoutCreateRequest));
  }

  public ResponseEntity<CheckoutResponse> completeCheckout(
      String requestSignature,
      UUID idempotencyKey,
      UUID requestId,
      String ucPAgent,
      String id,
      CompleteCheckoutRequest completeCheckoutRequest,
      String authorization,
      String xAPIKey,
      String userAgent,
      String contentType,
      String accept,
      String acceptLanguage,
      String acceptEncoding) {
    UcpAgentInfo agentInfo = parseAndValidateUcpAgentHeader(ucPAgent);
    return ResponseEntity.ok(
        completeCheckoutAction.completeCheckout(
            id,
            idempotencyKey,
            completeCheckoutRequest,
            platformProfileResolver.resolveWebhookUrl(agentInfo.profile).orElse(null)));
  }

  @Override
  public ResponseEntity<CheckoutResponse> cancelCheckout(
      String requestSignature,
      UUID idempotencyKey,
      UUID requestId,
      String ucPAgent,
      String id,
      String authorization,
      String xAPIKey,
      String userAgent,
      String contentType,
      String accept,
      String acceptLanguage,
      String acceptEncoding) {
    parseAndValidateUcpAgentHeader(ucPAgent);
    return ResponseEntity.ok(cancelCheckoutAction.cancelCheckout(id, idempotencyKey));
  }

  @Override
  public ResponseEntity<CheckoutResponse> updateCheckout(
      String requestSignature,
      UUID idempotencyKey,
      UUID requestId,
      String ucPAgent,
      String id,
      CheckoutUpdateRequest checkout,
      String authorization,
      String xAPIKey,
      String userAgent,
      String contentType,
      String accept,
      String acceptLanguage,
      String acceptEncoding) {
    parseAndValidateUcpAgentHeader(ucPAgent);
    return ResponseEntity.ok(updateCheckoutAction.updateCheckout(id, idempotencyKey, checkout));
  }

  @Override
  public ResponseEntity<CheckoutResponse> getCheckout(
      String requestSignature,
      UUID requestId,
      String ucPAgent,
      String id,
      String authorization,
      String xAPIKey,
      String userAgent,
      String contentType,
      String accept,
      String acceptLanguage,
      String acceptEncoding) {
    parseAndValidateUcpAgentHeader(ucPAgent);
    return ResponseEntity.ok(getCheckoutAction.getCheckout(id));
  }
}
