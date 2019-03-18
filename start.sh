#!/bin/bash

##################################################
# Copyright (c) 2019 Zhao Xiang Lim.
# Distributed under the Apache License 2.0 (the "License").
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# You should have received a copy of the Apache License 2.0
# along with this program.
# If not, see <http://www.apache.org/licenses/LICENSE-2.0>.
##################################################


clean_pycache () {
	sleep 1
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
}


if command -v gunicorn >/dev/null 2>&1; then
	gunicorn --workers 3 --bind 0.0.0.0:8080 start:app
	echo "[*] Cleaning up..."
	clean_pycache
else
	echo "[!] Please install all required modules in requirements.txt, preferably in a Python virtual environment."
fi