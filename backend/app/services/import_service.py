import pandas as pd
from typing import List, Dict, Any, Tuple
from io import BytesIO
from datetime import datetime
from decimal import Decimal


class ImportValidationError:
    def __init__(self, row: int, field: str, error: str):
        self.row = row
        self.field = field
        self.error = error

    def to_dict(self):
        return {
            "row": self.row,
            "field": self.field,
            "error": self.error
        }


class ImportService:
    """Service for validating and processing CSV/Excel imports"""

    @staticmethod
    def validate_historical_projects(file_content: bytes, filename: str) -> Tuple[List[Dict[str, Any]], List[ImportValidationError]]:
        """
        Validate historical projects CSV/Excel file
        Returns: (valid_rows, errors)
        """
        errors = []
        valid_rows = []

        try:
            # Read file based on extension
            if filename.endswith('.csv'):
                df = pd.read_csv(BytesIO(file_content))
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(BytesIO(file_content))
            else:
                raise ValueError("Unsupported file format. Use CSV or Excel.")

            # Required fields
            required_fields = ['name', 'job_number']

            # Check for required columns
            missing_cols = [col for col in required_fields if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

            # Validate each row
            for idx, row in df.iterrows():
                row_num = idx + 2  # +2 for header and 0-indexing
                row_errors = []

                # Validate required fields
                if pd.isna(row['name']) or str(row['name']).strip() == '':
                    row_errors.append(ImportValidationError(row_num, 'name', 'Name is required'))

                if pd.isna(row['job_number']) or str(row['job_number']).strip() == '':
                    row_errors.append(ImportValidationError(row_num, 'job_number', 'Job number is required'))

                # Validate date format
                if 'completion_date' in df.columns and not pd.isna(row['completion_date']):
                    try:
                        pd.to_datetime(row['completion_date'])
                    except:
                        row_errors.append(ImportValidationError(row_num, 'completion_date', 'Invalid date format'))

                # Validate numeric fields
                numeric_fields = ['original_bid', 'final_cost', 'profit_margin']
                for field in numeric_fields:
                    if field in df.columns and not pd.isna(row[field]):
                        try:
                            float(row[field])
                        except:
                            row_errors.append(ImportValidationError(row_num, field, 'Must be a number'))

                # Validate profit margin range
                if 'profit_margin' in df.columns and not pd.isna(row['profit_margin']):
                    try:
                        margin = float(row['profit_margin'])
                        if margin < -100 or margin > 100:
                            row_errors.append(ImportValidationError(row_num, 'profit_margin', 'Must be between -100 and 100'))
                    except:
                        pass  # Already caught above

                if row_errors:
                    errors.extend(row_errors)
                else:
                    # Prepare valid row data
                    valid_row = {
                        'name': str(row['name']).strip(),
                        'job_number': str(row['job_number']).strip(),
                        'completion_date': pd.to_datetime(row['completion_date']).date() if 'completion_date' in df.columns and not pd.isna(row['completion_date']) else None,
                        'original_bid': Decimal(str(row['original_bid'])) if 'original_bid' in df.columns and not pd.isna(row['original_bid']) else None,
                        'final_cost': Decimal(str(row['final_cost'])) if 'final_cost' in df.columns and not pd.isna(row['final_cost']) else None,
                        'profit_margin': Decimal(str(row['profit_margin'])) if 'profit_margin' in df.columns and not pd.isna(row['profit_margin']) else None,
                        'import_source': row.get('import_source', 'csv'),
                        'notes': str(row['notes']).strip() if 'notes' in df.columns and not pd.isna(row['notes']) else None
                    }
                    valid_rows.append(valid_row)

        except Exception as e:
            errors.append(ImportValidationError(0, 'file', str(e)))

        return valid_rows, errors

    @staticmethod
    def validate_historical_estimates(file_content: bytes, filename: str) -> Tuple[List[Dict[str, Any]], List[ImportValidationError]]:
        """
        Validate historical estimates CSV/Excel file
        Returns: (valid_rows, errors)
        """
        errors = []
        valid_rows = []

        try:
            # Read file based on extension
            if filename.endswith('.csv'):
                df = pd.read_csv(BytesIO(file_content))
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(BytesIO(file_content))
            else:
                raise ValueError("Unsupported file format. Use CSV or Excel.")

            # Required fields
            required_fields = ['description', 'quantity', 'unit']

            # Check for required columns
            missing_cols = [col for col in required_fields if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

            # Validate each row
            for idx, row in df.iterrows():
                row_num = idx + 2
                row_errors = []

                # Validate required fields
                if pd.isna(row['description']) or str(row['description']).strip() == '':
                    row_errors.append(ImportValidationError(row_num, 'description', 'Description is required'))

                if pd.isna(row['quantity']):
                    row_errors.append(ImportValidationError(row_num, 'quantity', 'Quantity is required'))
                else:
                    try:
                        qty = float(row['quantity'])
                        if qty <= 0:
                            row_errors.append(ImportValidationError(row_num, 'quantity', 'Must be greater than 0'))
                    except:
                        row_errors.append(ImportValidationError(row_num, 'quantity', 'Must be a number'))

                if pd.isna(row['unit']) or str(row['unit']).strip() == '':
                    row_errors.append(ImportValidationError(row_num, 'unit', 'Unit is required'))

                # Validate numeric fields
                numeric_fields = ['materials_cost', 'labor_hours', 'labor_cost', 'equipment_cost', 'productivity_rate']
                for field in numeric_fields:
                    if field in df.columns and not pd.isna(row[field]):
                        try:
                            val = float(row[field])
                            if val < 0:
                                row_errors.append(ImportValidationError(row_num, field, 'Cannot be negative'))
                        except:
                            row_errors.append(ImportValidationError(row_num, field, 'Must be a number'))

                if row_errors:
                    errors.extend(row_errors)
                else:
                    # Prepare valid row data
                    valid_row = {
                        'bid_item_code': str(row['bid_item_code']).strip() if 'bid_item_code' in df.columns and not pd.isna(row['bid_item_code']) else None,
                        'description': str(row['description']).strip(),
                        'quantity': Decimal(str(row['quantity'])),
                        'unit': str(row['unit']).strip(),
                        'job_number': str(row['job_number']).strip() if 'job_number' in df.columns and not pd.isna(row['job_number']) else None,
                        'materials_cost': Decimal(str(row['materials_cost'])) if 'materials_cost' in df.columns and not pd.isna(row['materials_cost']) else None,
                        'labor_hours': Decimal(str(row['labor_hours'])) if 'labor_hours' in df.columns and not pd.isna(row['labor_hours']) else None,
                        'labor_cost': Decimal(str(row['labor_cost'])) if 'labor_cost' in df.columns and not pd.isna(row['labor_cost']) else None,
                        'equipment_cost': Decimal(str(row['equipment_cost'])) if 'equipment_cost' in df.columns and not pd.isna(row['equipment_cost']) else None,
                        'productivity_rate': Decimal(str(row['productivity_rate'])) if 'productivity_rate' in df.columns and not pd.isna(row['productivity_rate']) else None,
                        'notes': str(row['notes']).strip() if 'notes' in df.columns and not pd.isna(row['notes']) else None
                    }
                    valid_rows.append(valid_row)

        except Exception as e:
            errors.append(ImportValidationError(0, 'file', str(e)))

        return valid_rows, errors

    @staticmethod
    def generate_projects_template() -> bytes:
        """Generate CSV template for historical projects import"""
        df = pd.DataFrame(columns=[
            'name',
            'job_number',
            'completion_date',
            'original_bid',
            'final_cost',
            'profit_margin',
            'import_source',
            'notes'
        ])

        # Add example row
        df.loc[0] = [
            'Highway 101 Widening',
            'JOB-2023-001',
            '2023-12-31',
            '1500000',
            '1450000',
            '3.45',
            'csv',
            'Completed ahead of schedule'
        ]

        # Convert to CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return output.getvalue()

    @staticmethod
    def generate_estimates_template() -> bytes:
        """Generate CSV template for historical estimates import"""
        df = pd.DataFrame(columns=[
            'job_number',
            'bid_item_code',
            'description',
            'quantity',
            'unit',
            'materials_cost',
            'labor_hours',
            'labor_cost',
            'equipment_cost',
            'productivity_rate',
            'notes'
        ])

        # Add example row
        df.loc[0] = [
            'JOB-2023-001',
            '203-01',
            'Excavation (Common)',
            '5000',
            'CY',
            '25000',
            '200',
            '8000',
            '12000',
            '25',
            'Used 2 excavators'
        ]

        # Convert to CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return output.getvalue()
