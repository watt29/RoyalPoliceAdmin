import re

class SmartParserUtils:
    @staticmethod
    def split_mashed_numbers(num_str):
        """
        Intelligence: Split mashed numbers like '16016' into [total, inuse, instock]
        Formula: total = inuse + instock
        """
        s = str(num_str).strip().replace(',', '')
        if not s.isdigit() or len(s) < 2:
            return None
        n = len(s)
        for i in range(1, n):
            for j in range(i + 1, n):
                first, second, third = s[:i], s[i:j], s[j:]
                # Skip if leading zeros (except "0" itself)
                if len(first) > 1 and first[0] == '0': continue
                if len(second) > 1 and second[0] == '0': continue
                if len(third) > 1 and third[0] == '0': continue
                try:
                    a, b, c = int(first), int(second), int(third)
                    if a == b + c:
                        return [a, b, c]
                except ValueError:
                    continue
        return None

    @staticmethod
    def detect_index_shift(parts, col_map, target_sheet):
        """
        Intelligence: Detect if the first column is a row index (1, 2, 3) 
        and shift indices if header mapping didn't account for it.
        """
        if not parts or not col_map:
            return 0
            
        first_val = parts[0].strip()
        if first_val.isdigit():
            val = int(first_val)
            # Typically index is 1-100 and it wasn't mapped as the main name/type
            if 0 < val <= 500:
                # Check if col 0 is mapped to name/type/date but data here is just a small number
                if target_sheet == "Equipment" and col_map.get('eq_type') == 0:
                    return 1
                if target_sheet == "Contacts" and col_map.get('name') == 0:
                    return 1
                if target_sheet == "DutyRoster" and col_map.get('date') == 0:
                    return 1
        return 0

    @staticmethod
    def clean_num(s):
        """Clean commas, asterisks and extra text to extract pure digits."""
        if s is None: return "0"
        s = str(s)
        res = "".join(filter(str.isdigit, s.replace('*','').replace(',','')))
        return res if res else "0"

    @staticmethod
    def is_position_or_agency(text):
        """Detect if text is likely a position or an agency (e.g. 'ผบ.หมู่', 'สภ.')."""
        if not text: return False
        keywords = ["ผบ.หมู่", "สภ.", "บางบาล", "บางปะอิน", "วังน้อย", "รอง สว.", "สว.", "ผบก.", "สวพ."]
        return any(k in text for k in keywords)

class LogicUtils:
    @staticmethod
    def parse_thai_date(text):
        """Very basic Thai date parser for simple contexts."""
        if not text: return None
        # Placeholder for future expansion
        return text.strip()
