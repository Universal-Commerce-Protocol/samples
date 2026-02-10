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
import type React from 'react';
import type {Booking} from '../types';

interface BookingCardProps {
  booking: Booking;
}

const BookingCard: React.FC<BookingCardProps> = ({booking}) => {
  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return {
      date: date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      }),
      time: date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      }),
    };
  };

  const formatAddress = (location?: Booking['location']) => {
    if (!location?.address) return null;
    const addr = location.address;
    const parts = [
      addr.address_line_1,
      [addr.locality, addr.administrative_district_level_1].filter(Boolean).join(', '),
    ].filter(Boolean);
    return parts.join(', ');
  };

  const {date, time} = formatDateTime(booking.start_at);

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden w-full max-w-md border border-green-200">
      <div className="bg-green-500 text-white px-4 py-3 flex items-center">
        <svg
          className="w-6 h-6 mr-2"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 13l4 4L19 7"
          />
        </svg>
        <span className="font-semibold text-lg">Booking Confirmed</span>
      </div>
      <div className="p-4 space-y-4">
        <div className="flex items-start">
          <svg
            className="w-5 h-5 mr-3 text-gray-500 mt-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <div>
            <p className="font-semibold text-gray-800">{date}</p>
            <p className="text-gray-600">{time}</p>
          </div>
        </div>

        {booking.location && (
          <div className="flex items-start">
            <svg
              className="w-5 h-5 mr-3 text-gray-500 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            <div>
              <p className="font-semibold text-gray-800">{booking.location.name}</p>
              {formatAddress(booking.location) && (
                <p className="text-gray-600 text-sm">{formatAddress(booking.location)}</p>
              )}
            </div>
          </div>
        )}

        {booking.services && booking.services.length > 0 && (
          <div className="flex items-start">
            <svg
              className="w-5 h-5 mr-3 text-gray-500 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            <div>
              <p className="font-semibold text-gray-800">Services</p>
              <ul className="text-gray-600 text-sm">
                {booking.services.map((service) => (
                  <li key={service.id}>{service.name}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {booking.staff && booking.staff.length > 0 && (
          <div className="flex items-start">
            <svg
              className="w-5 h-5 mr-3 text-gray-500 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
            <div>
              <p className="font-semibold text-gray-800">Staff</p>
              <ul className="text-gray-600 text-sm">
                {booking.staff.map((member) => (
                  <li key={member.id}>{member.display_name || 'Any available'}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {booking.customer_note && (
          <div className="flex items-start">
            <svg
              className="w-5 h-5 mr-3 text-gray-500 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
              />
            </svg>
            <div>
              <p className="font-semibold text-gray-800">Notes</p>
              <p className="text-gray-600 text-sm">{booking.customer_note}</p>
            </div>
          </div>
        )}

        <div className="border-t pt-3 mt-3">
          <p className="text-xs text-gray-400 text-center">
            Booking ID: {booking.id}
          </p>
        </div>
      </div>
    </div>
  );
};

export default BookingCard;
