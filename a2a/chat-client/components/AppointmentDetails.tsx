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
import type {Appointment} from '../types';

interface AppointmentDetailsProps {
  appointment: Appointment;
}

const AppointmentDetails: React.FC<AppointmentDetailsProps> = ({appointment}) => {
  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return {
      date: date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      }),
      time: date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      }),
    };
  };

  return (
    <div className="border-t mt-3 pt-3">
      <h4 className="text-sm font-semibold text-gray-700 flex items-center mb-2">
        <svg
          className="w-4 h-4 mr-2"
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
        Appointment Details
      </h4>

      {appointment.slots.map((slot, index) => {
        const selectedOption = slot.options.find(
          opt => opt.id === slot.selected_option_id
        ) || slot.options[0];

        if (!selectedOption) return null;

        const {date, time} = formatDateTime(selectedOption.start_time);

        return (
          <div
            key={slot.id || index}
            className="bg-gray-50 rounded-md p-2 mb-2 last:mb-0">
            {slot.location && (
              <div className="flex items-center text-sm text-gray-600 mb-2">
                <svg
                  className="w-4 h-4 mr-2"
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
                <span>{slot.location.name}</span>
              </div>
            )}
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center text-gray-700">
                <svg
                  className="w-4 h-4 mr-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span>
                  {date} at {time}
                </span>
              </div>
              {selectedOption.duration_minutes && (
                <span className="text-xs text-gray-500">
                  {selectedOption.duration_minutes} min
                </span>
              )}
            </div>
            {selectedOption.staff_name && (
              <p className="text-xs text-gray-500 mt-1 ml-5">
                with {selectedOption.staff_name}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default AppointmentDetails;
