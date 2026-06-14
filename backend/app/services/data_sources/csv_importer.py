"""CSV importer for manual NSE stock data import."""
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from app.models.ohlcv import OHLCVRecord


logger = logging.getLogger(__name__)


class CSVImporter:
    """Importer for NSE stock data from CSV files."""
    
    # Expected CSV columns
    REQUIRED_COLUMNS = {'date', 'open', 'high', 'low', 'close', 'volume'}
    
    def import_file(self, filepath: Path, symbol: str) -> List[OHLCVRecord]:
        """
        Import OHLCV data from a CSV file.
        
        Expected CSV format:
            date,open,high,low,close,volume
            2024-01-01,100.0,105.0,99.0,103.0,1000000
        
        Args:
            filepath: Path to CSV file
            symbol: Stock symbol (e.g., "SCOM.NR")
        
        Returns:
            List of OHLCVRecord objects
        
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        if not filepath.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")
        
        try:
            logger.info(f"Importing {symbol} data from {filepath}")
            
            records = []
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                
                # Validate columns
                if not reader.fieldnames:
                    raise ValueError("CSV file is empty or has no header")
                
                columns = set(col.lower().strip() for col in reader.fieldnames)
                missing_columns = self.REQUIRED_COLUMNS - columns
                
                if missing_columns:
                    raise ValueError(
                        f"CSV missing required columns: {missing_columns}. "
                        f"Expected columns: {self.REQUIRED_COLUMNS}"
                    )
                
                # Parse rows
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Normalize column names (case-insensitive)
                        row = {k.lower().strip(): v.strip() for k, v in row.items()}
                        
                        # Parse date
                        try:
                            record_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                        except ValueError:
                            # Try alternative date format
                            record_date = datetime.strptime(row['date'], '%m/%d/%Y').date()
                        
                        # Create OHLCV record
                        record = OHLCVRecord(
                            symbol=symbol if symbol.endswith('.NR') else f"{symbol}.NR",
                            date=record_date,
                            open=float(row['open']),
                            high=float(row['high']),
                            low=float(row['low']),
                            close=float(row['close']),
                            volume=int(float(row['volume'])),
                            currency='KES',
                            market='NSE'
                        )
                        
                        records.append(record)
                        
                    except KeyError as e:
                        logger.warning(f"Row {row_num}: Missing column {e}")
                        continue
                    except ValueError as e:
                        logger.warning(f"Row {row_num}: Invalid data format - {e}")
                        continue
                    except Exception as e:
                        logger.warning(f"Row {row_num}: Failed to parse - {e}")
                        continue
            
            # Sort by date ascending
            records.sort(key=lambda r: r.date)
            
            logger.info(f"Imported {len(records)} records for {symbol} from CSV")
            return records
            
        except csv.Error as e:
            logger.error(f"CSV parsing error: {e}")
            raise ValueError(f"Invalid CSV format: {e}")
        except Exception as e:
            logger.error(f"Failed to import CSV: {e}")
            raise
