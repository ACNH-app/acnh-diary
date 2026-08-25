import { Search } from "lucide-react";

type SearchFieldProps = {
  placeholder: string;
  value?: string;
  onChange?: (value: string) => void;
};

export function SearchField({ placeholder, value = "", onChange }: SearchFieldProps) {
  return (
    <label className="search-field">
      <Search aria-hidden="true" size={18} />
      <input
        aria-label={placeholder}
        onChange={(event) => onChange?.(event.target.value)}
        placeholder={placeholder}
        value={value}
      />
    </label>
  );
}
