# Copyright Quantinuum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass
from typing import Any, ClassVar

from pytket.config import PytketExtConfig


@dataclass
class IQMConfig(PytketExtConfig):
    """Holds config parameters for pytket-iqm."""

    ext_dict_key: ClassVar[str] = "iqm"

    api_token: str | None

    @classmethod
    def from_extension_dict(
        cls: type["IQMConfig"], ext_dict: dict[str, Any]
    ) -> "IQMConfig":
        return cls(ext_dict.get("api_token"))


def set_iqm_config(api_token: str | None = None) -> None:
    """Set default value for IQM API token."""
    config: IQMConfig = IQMConfig.from_default_config_file()
    if api_token is not None:
        config.api_token = api_token
    config.update_default_config_file()
