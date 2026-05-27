"use client";

interface Props {
  suggestions: string[];
  onSelect: (text: string) => void;
  disabled?: boolean;
}

export default function SuggestionChips({ suggestions, onSelect, disabled }: Props) {
  if (!suggestions.length) return null;

  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {suggestions.map((s, i) => (
        <button
          key={i}
          onClick={() => onSelect(s)}
          disabled={disabled}
          className="text-xs px-3 py-1.5 rounded-full border border-gray-200
                     bg-white hover:bg-gray-100 hover:border-gray-300
                     disabled:opacity-40 disabled:cursor-not-allowed
                     transition-colors text-gray-700"
        >
          {s}
        </button>
      ))}
    </div>
  );
}
