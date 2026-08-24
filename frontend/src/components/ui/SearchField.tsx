import { Search } from "lucide-react";

type SearchFieldProps = {
  placeholder: string;
};

export function SearchField({ placeholder }: SearchFieldProps) {
  return (
    <label className="search-field">
      <Search aria-hidden="true" size={18} />
      <input aria-label={placeholder} placeholder={placeholder} />
    </label>
  );
}
