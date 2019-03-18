#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


from pyHookDeploy import init_app


app = init_app()


def main():
	# Run instance on 0.0.0.0 on port 5000.
	app.run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
	main()
