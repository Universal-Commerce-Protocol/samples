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
export enum Sender {
  USER = 'user',
  MODEL = 'model',
}

export interface Product {
  productID: string;
  name: string;
  image: string[];
  brand: {name: string};
  offers: {
    price: string;
    priceCurrency: string;
    availability: string;
  };
  url: string;
  description: string;
  size: {
    name: string;
  };
}

export interface Credential {
  type: string;
  token: string;
}

export interface PaymentMethod {
  id: string;
  type: string;
  brand: string;
  last_digits: string;
  expiry_month: number;
  expiry_year: number;
}

export interface PaymentInstrument extends PaymentMethod {
  handler_id: string;
  handler_name: string;
  credential: Credential;
}

export interface ChatMessage {
  id: string;
  sender: Sender;
  text: string;
  products?: Product[];
  isLoading?: boolean;
  paymentMethods?: PaymentMethod[];
  isUserAction?: boolean;
  checkout?: Checkout;
  paymentInstrument?: PaymentInstrument;
  services?: ServiceVariation[];
  locations?: Location[];
  staff?: StaffResponse[];
  availabilitySlots?: AvailabilitySlot[];
  bookings?: Booking[];
}


export interface CheckoutTotal {
  type: string;
  display_text: string;
  amount: number;
}

export interface CheckoutItem {
  id: string;
  item: {
    id: string;
    title: string;
    price: number;
    image_url: string;
  };
  quantity: number;
  totals: CheckoutTotal[];
}

export interface PaymentHandler {
  id: string;
  name: string;
  //...other props
}
export interface Payment {
  handlers: PaymentHandler[];
  selected_instrument_id: string;
  instruments: PaymentInstrument[];
}

export interface Checkout {
  id: string;
  line_items: CheckoutItem[];
  currency: string;
  continue_url?: string | null;
  status: string;
  totals: CheckoutTotal[];
  order_id?: string;
  order_permalink_url?: string;
  payment?: Payment;
  appointment?: Appointment;
}

// Location types
export interface Coordinate {
  latitude: number;
  longitude: number;
}

export interface Address {
  address_line_1?: string;
  address_line_2?: string;
  // New backend fields
  city?: string;
  state?: string;
  zip_code?: string;
  // Legacy fields
  locality?: string;
  administrative_district_level_1?: string;
  postal_code?: string;
  country?: string;
}

export interface Location {
  id: string;
  name: string;
  address?: Address;
  timezone?: string;
  coordinates?: Coordinate;
  description?: string;
}

export interface LocationSummary {
  id: string;
  name: string;
  address?: Address;
}

// Staff types
export interface StaffSummaryResponse {
  id: string;
  // New backend fields
  name?: string;
  first_name?: string;
  last_name?: string;
  available_at?: LocationSummary[];
  // Legacy field
  display_name?: string;
}

export interface StaffResponse {
  id: string;
  // New backend fields
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  status?: string;
  locations?: LocationSummary[];
  // Legacy fields
  display_name?: string;
  email_address?: string;
  phone_number?: string;
  is_available?: boolean;
}

// Service types
export interface ServiceVariation {
  id: string;
  service_id?: string;
  name: string;
  description?: string | null;
  display_price?: string;
  price?: number;
  duration_seconds?: number;
  staff?: StaffSummaryResponse[] | null;
  // Legacy fields for backwards compatibility
  price_money?: {
    amount: number;
    currency: string;
  };
  service_duration?: number;
  available_for_booking?: boolean;
  image_url?: string;
}

// Availability types
export interface AvailabilitySlot {
  start_time: string;
  end_time?: string;
  staff?: StaffSummaryResponse;
  location?: LocationSummary;
  // Legacy fields for backwards compatibility
  start_at?: string;
  location_id?: string;
  appointment_segments?: {
    duration_minutes: number;
    team_member_id: string;
    service_variation_id: string;
    service_variation_version?: number;
  }[];
}

// Booking types
export interface Customer {
  id?: string;
  // New backend fields
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  // Legacy fields
  given_name?: string;
  family_name?: string;
  email_address?: string;
  phone_number?: string;
}

export interface AppointmentSegment {
  duration_minutes: number;
  service_variation_id: string;
  team_member_id: string;
  service_variation_version?: number;
}

export interface Booking {
  id: string;
  // New backend fields
  start_time?: string;
  duration_minutes?: number;
  segments?: AppointmentSegment[];
  customer_notes?: string;
  seller_notes?: string;
  // Existing/Legacy fields
  version?: number;
  status?: string;
  created_at?: string;
  updated_at?: string;
  start_at?: string;
  location_id?: string;
  customer_id?: string;
  customer_note?: string;
  seller_note?: string;
  appointment_segments?: AppointmentSegment[];
  location?: Location;
  customer?: Customer;
  staff?: StaffSummaryResponse[];
  services?: { id: string; name: string }[];
}

// Appointment checkout types
export interface AppointmentSlotOption {
  id: string;
  start_time: string;
  end_time?: string;
  staff_id?: string;
  staff_name?: string | null;
  duration_minutes?: number;
}

export interface AppointmentSlot {
  id: string;
  line_item_ids?: string[];
  location?: {
    id: string;
    name: string;
    address?: Address | null;
  };
  options: AppointmentSlotOption[];
  selected_option_id?: string;
  notes?: string | null;
}

export interface Appointment {
  slots: AppointmentSlot[];
}
