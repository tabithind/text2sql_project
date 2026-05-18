import pandas as pd
import os

class ExportService:
    @staticmethod
    def export_to_csv(columns: list, rows: list, filepath: str) -> dict:
        try:
            df = pd.DataFrame(rows, columns=columns)
            
            # Create exports directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            df.to_csv(filepath, index=False, encoding='utf-8')
            return {'ok': True, 'filepath': filepath}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    @staticmethod
    def export_to_excel(columns: list, rows: list, filepath: str) -> dict:
        try:
            df = pd.DataFrame(rows, columns=columns)
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            df.to_excel(filepath, index=False, engine='openpyxl')
            return {'ok': True, 'filepath': filepath}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}
