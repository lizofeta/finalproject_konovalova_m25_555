import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from valutatrade_hub.parser_service.config import ParserConfig


class HistoryStorage:
    def __init__(self, config: ParserConfig):
        self.config = config
        self.file = config.HISTORY_FILE_PATH
        self.file.parent.mkdir(parents=True, exist_ok=True)
    
    def append(self, records:list):
        """
        Метод для добавления новых записей.
        """
        existing = []
        if self.file.exists() and self.file.stat().st_size > 0:
            existing = json.loads(self.file.read_text(encoding='utf-8'))
        
        existing.extend(records)

        self._atomic_write(existing)
    
    def _atomic_write(self, data):
        """
        Метод для реализации атомарной записи в файл exchange_rates.json.
        Принцип: файл либо полностью иобновлен, либо не изменяется вообще.
        """
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', delete=False, dir=self.file.parent
        ) as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=4)
            tmp_path = Path(tmp.name)
        tmp_path.replace(self.file)


class RatesStorage:
    def __init__(self, config: ParserConfig):
        self.config = config
        self.file = config.RATES_FILE_PATH
        self.file.parent.mkdir(parents=True, exist_ok=True)
    
    def save_rates(self, pairs:dict):
        if not isinstance(pairs, dict):
            raise TypeError\
                ('Данные о курсах валют должны передаваться в словаре.')
        data = {
            'rates': pairs,
            'last_refresh': datetime.now(timezone.utc)\
                .replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        }
        self._atomic_write(data)

    def _atomic_write(self, data):
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', delete=False, dir=self.file.parent 
        ) as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=4)
            tmp_path = Path(tmp.name)
        tmp_path.replace(self.file)