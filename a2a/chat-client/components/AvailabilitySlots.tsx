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
import {useState} from 'react';
import type {AvailabilitySlot} from '../types';

interface AvailabilitySlotsProps {
  slots: AvailabilitySlot[];
  onSelectSlot?: (slot: AvailabilitySlot) => void;
}

const AvailabilitySlots: React.FC<AvailabilitySlotsProps> = ({
  slots,
  onSelectSlot,
}) => {
  const [selectedSlot, setSelectedSlot] = useState<AvailabilitySlot | null>(null);

  const getStartTime = (slot: AvailabilitySlot): string => {
    return slot.start_time || slot.start_at || '';
  };

  const groupSlotsByDate = (
    slots: AvailabilitySlot[],
  ): Map<string, AvailabilitySlot[]> => {
    const groups = new Map<string, AvailabilitySlot[]>();
    for (const slot of slots) {
      const startTime = getStartTime(slot);
      if (!startTime) continue;
      const date = new Date(startTime).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
      if (!groups.has(date)) {
        groups.set(date, []);
      }
      groups.get(date)?.push(slot);
    }
    return groups;
  };

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const handleSlotClick = (slot: AvailabilitySlot) => {
    setSelectedSlot(slot);
  };

  const handleConfirm = () => {
    if (selectedSlot && onSelectSlot) {
      onSelectSlot(selectedSlot);
    }
  };

  const groupedSlots = groupSlotsByDate(slots);

  if (slots.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 max-w-md">
        <p className="text-gray-600">No available time slots found.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden max-w-lg">
      <div className="bg-blue-500 text-white px-4 py-3 flex items-center">
        <svg
          className="w-5 h-5 mr-2"
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
        <span className="font-semibold">Available Times</span>
      </div>
      <div className="p-4 max-h-80 overflow-y-auto">
        {Array.from(groupedSlots.entries()).map(([date, dateSlots]) => (
          <div key={date} className="mb-4 last:mb-0">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">{date}</h4>
            <div className="grid grid-cols-3 gap-2">
              {dateSlots.map((slot, index) => {
                const slotStart = getStartTime(slot);
                const selectedStart = selectedSlot ? getStartTime(selectedSlot) : '';
                const slotLocationId = slot.location?.id || slot.location_id;
                const selectedLocationId = selectedSlot?.location?.id || selectedSlot?.location_id;
                const isSelected =
                  selectedStart === slotStart &&
                  selectedLocationId === slotLocationId;
                return (
                  <button
                    key={`${slotStart}-${slotLocationId}-${index}`}
                    type="button"
                    onClick={() => handleSlotClick(slot)}
                    className={`px-3 py-2 text-sm rounded-md transition-colors ${
                      isSelected
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}>
                    {formatTime(slotStart)}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      {selectedSlot && (
        <div className="border-t p-4">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              <p className="font-medium text-gray-800">
                Selected: {formatTime(getStartTime(selectedSlot))}
              </p>
              {selectedSlot.staff?.name && (
                <p>Staff: {selectedSlot.staff.name}</p>
              )}
              {selectedSlot.location?.name && (
                <p>Location: {selectedSlot.location.name}</p>
              )}
            </div>
            {onSelectSlot && (
              <button
                type="button"
                onClick={handleConfirm}
                className="bg-green-500 text-white px-4 py-2 rounded-md hover:bg-green-600 transition-colors">
                Confirm Time
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AvailabilitySlots;
