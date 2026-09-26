#!/usr/bin/env bash
set -euo pipefail

gem5_commit=d4efbee56d71f9609eab85393eff58f5dbf7763c
aladdin_commit=448b8f41865003e20eee0bdbd7a73febb5c3abe3
patch=/project/patches/bounded_queue_gemm_pilot.patch

if [[ ! -d /worksrc/.git ]]; then
  git clone https://github.com/harvard-acc/gem5-aladdin.git /worksrc
fi
cd /worksrc
git checkout --detach "$gem5_commit"
git submodule update --init src/aladdin ext/fp16
[[ $(git rev-parse HEAD) == "$gem5_commit" ]]
[[ $(git -C src/aladdin rev-parse HEAD) == "$aladdin_commit" ]]

if git -C src/aladdin apply --reverse --check "$patch" 2>/dev/null; then
  echo 'Finite-queue patch already applied.'
else
  git -C src/aladdin apply --check "$patch"
  git -C src/aladdin apply "$patch"
fi

scons build/X86/gem5.opt -j6 PROTOCOL=MESI_Two_Level_aladdin
test -x build/X86/gem5.opt
