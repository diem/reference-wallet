# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

(cd backend && exec pipenv run black .)

(cd frontend && exec yarn prettier --write .)

(cd vasp-validator && exec ./lint.sh)