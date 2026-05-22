"""
config_loader.py — Centralized Configuration Loader

Loads all external config files and environment variables.
Exposes configurable field names, contractor codes, role maps, and DB config.
Nothing is hardcoded in rule logic — all business values come from here.
"""

import os
import logging
import pandas as pd
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)

# Load .env from project root
load_dotenv(find_dotenv())


class Config:
    """Immutable, centralized configuration for the IAI Agent."""

    def __init__(self, base_dir: str = None):
        # Resolve project root
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = base_dir
        self.data_dir = os.path.join(self.base_dir, "Data")

        # --- Environment Variables ---
        self.database_url: str = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/iai_db"
        )
        self.psid_field_name: str = os.getenv("PSID_FIELD_NAME", "Emplid")
        self.rm_notification_url: str = os.getenv("RM_NOTIFICATION_URL", "")
        self.output_dir: str = os.path.join(
            self.base_dir, os.getenv("OUTPUT_DIR", "Data")
        )
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        # --- File Paths ---
        self.ris_path: str = os.path.join(self.data_dir, "RIS_Synthetic.xlsx")
        self.so_path: str = os.path.join(self.data_dir, "SO_Ageing_Synthetic.xlsx")
        self.contractor_cfg_path: str = os.path.join(self.data_dir, "contractor_config.csv")
        self.role_cfg_path: str = os.path.join(self.data_dir, "role_mapping_config.csv")
        self.merged_path: str = os.path.join(self.data_dir, "Merged_Prepared_Data.csv")

        # --- Loaded Config Data (populated by load()) ---
        self._contractor_codes: frozenset = frozenset()
        self._support_sales_roles: frozenset = frozenset()
        self._loaded: bool = False

    def load(self) -> "Config":
        """Load all external config files. Must be called before accessing config data."""
        self._load_contractor_codes()
        self._load_support_sales_roles()
        self._loaded = True
        logger.info(
            f"Config loaded: {len(self._contractor_codes)} contractor codes, "
            f"{len(self._support_sales_roles)} support/sales roles, "
            f"PSID field='{self.psid_field_name}'"
        )
        return self

    def _load_contractor_codes(self):
        """Load contractor category codes from CSV/Excel config file."""
        try:
            if self.contractor_cfg_path.endswith(".csv"):
                df = pd.read_csv(self.contractor_cfg_path)
            else:
                df = pd.read_excel(self.contractor_cfg_path)

            col = df.columns[0]  # Use first column regardless of name
            codes = df[col].dropna().astype(str).str.strip().str.lower().tolist()
            self._contractor_codes = frozenset(codes)
            logger.info(f"Loaded {len(self._contractor_codes)} contractor category codes from {self.contractor_cfg_path}")
        except FileNotFoundError:
            logger.error(f"Contractor config file not found: {self.contractor_cfg_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading contractor config: {e}")
            raise

    def _load_support_sales_roles(self):
        """Load Support/Sales role names from CSV/Excel config file."""
        try:
            if self.role_cfg_path.endswith(".csv"):
                df = pd.read_csv(self.role_cfg_path)
            else:
                df = pd.read_excel(self.role_cfg_path)

            col = df.columns[0]  # Use first column regardless of name
            roles = df[col].dropna().astype(str).str.strip().str.lower().tolist()
            self._support_sales_roles = frozenset(roles)
            logger.info(f"Loaded {len(self._support_sales_roles)} support/sales roles from {self.role_cfg_path}")
        except FileNotFoundError:
            logger.error(f"Role mapping config file not found: {self.role_cfg_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading role mapping config: {e}")
            raise

    @property
    def contractor_codes(self) -> frozenset:
        if not self._loaded:
            raise RuntimeError("Config not loaded. Call config.load() first.")
        return self._contractor_codes

    @property
    def support_sales_roles(self) -> frozenset:
        if not self._loaded:
            raise RuntimeError("Config not loaded. Call config.load() first.")
        return self._support_sales_roles

    def to_dict(self) -> dict:
        """Return a serializable snapshot of the config for audit logging."""
        return {
            "psid_field_name": self.psid_field_name,
            "database_url": self.database_url.split("@")[-1] if self.database_url else "",  # Redact credentials
            "contractor_codes": sorted(list(self._contractor_codes)),
            "support_sales_roles": sorted(list(self._support_sales_roles)),
            "ris_path": self.ris_path,
            "so_path": self.so_path,
            "rm_notification_url": self.rm_notification_url or "(not configured)",
        }
