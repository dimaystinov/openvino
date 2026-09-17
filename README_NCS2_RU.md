# NCS2 в современном OpenVINO: форк для Roki

Этот форк добавляет обратно устройство **MYRIAD / Intel Neural Compute Stick 2**
как нативный плагин современного runtime. Основа — `master` OpenVINO с версией
**2026.5.0**, commit `311216b1296c0617f754abab8c87e100a2e8fac6`.
Программа робота: [roki_next_generation](https://github.com/dimaystinov/roki_next_generation).

Плагин находится в [`src/plugins/intel_myriad/`](src/plugins/intel_myriad/).
Он работает в процессе **нового Python с bindings этого же форка**.
Старый Python, OpenVINO 2022 runtime и сервис на старом Python не нужны.
В программе Roki этот процесс изолирован от управления роботом, чтобы
нативное падение или зависание NCS2 не завершало весь робот.

## Что реализовано

- Опциональная сборка `-DENABLE_INTEL_MYRIAD=ON`, по умолчанию OFF.
- Нативный `openvino_ncs2_plugin`, регистрация `MYRIAD` штатным механизмом
  OpenVINO, установка компонентом `myriad`.
- Включённый USB-транспорт mvnc/XLink из OpenVINO 2022.3.2, commit
  `e2c7e4d7b4d6b315c0b62a22438146b28d15f1ee`. Он собирается статически
  внутри нового плагина. Другой checkout OpenVINO для сборки этого плагина
  не нужен; исходники и лицензии транспорта сохранены.
- Импорт/экспорт статических MYRIAD `.blob` формата 6.0, чтение физических
  форм/типов тензоров, корректная передача padding/stride.
- Типы FP16, U8, I32, FP32, I8; проверки размеров, диапазонов и повреждений blob.
- Повторное использование infer request, стандартные sync/async API,
  сериализация пары USB queue/read между requests.
- Ошибка USB переводит сессию в неисправное состояние; повторный inference
  требует создания новой модели/сессии. Нативный I/O timeout — 10 секунд.
- Hardware-free тесты с отдельным тестовым плагином, который не устанавливается
  и не выдаётся за аппаратное выполнение сети.

**Ограничение:** `Core.compile_model(XML/ONNX, 'MYRIAD')` не реализован.
Используется `Core.import_model()` с заранее скомпилированным blob. Компилятор
из OpenVINO 2022.3 применяется только на машине подготовки модели; его перенос
в новое дерево — отдельная работа. Динамические формы, remote tensors,
profiling и восстановление внутреннего графа из blob не заявлены.
Автоматического CPU fallback нет. Целевой сценарий — один NCS2 и одна модель.

## Сборка runtime и Python

Собирать runtime, плагин и Python bindings **одного commit и ABI**.
Библиотека, собранная для 2026.0, не предназначена для загрузки в этот 2026.5
и наоборот. На Linux нужны CMake >= 3.26, C/C++17 toolchain, pkg-config,
libusb-1.0 development package, Python с development headers и numpy.

Пример минимальной конфигурации для blob runtime на машине сборки:

```sh
git clone https://github.com/dimaystinov/openvino.git
cd openvino
git submodule update --init thirdparty/pugixml thirdparty/json/nlohmann_json \
  thirdparty/ittapi/ittapi src/bindings/python/thirdparty/pybind11
cmake -S . -B build-ncs2 \
  -DCMAKE_BUILD_TYPE=Release -DTHREADING=SEQ \
  -DENABLE_INTEL_MYRIAD=ON \
  -DENABLE_INTEL_CPU=OFF -DENABLE_INTEL_GPU=OFF -DENABLE_INTEL_NPU=OFF \
  -DENABLE_AUTO=OFF -DENABLE_MULTI=OFF -DENABLE_AUTO_BATCH=OFF \
  -DENABLE_HETERO=OFF -DENABLE_TEMPLATE=OFF \
  -DENABLE_SAMPLES=OFF -DENABLE_TESTS=OFF \
  -DENABLE_PYTHON=ON -DENABLE_WHEEL=OFF -DENABLE_JS=OFF \
  -DENABLE_PROFILING_ITT=OFF -DENABLE_LTO=OFF \
  -DENABLE_OV_IR_FRONTEND=OFF -DENABLE_OV_ONNX_FRONTEND=OFF \
  -DENABLE_OV_PADDLE_FRONTEND=OFF -DENABLE_OV_PYTORCH_FRONTEND=OFF \
  -DENABLE_OV_JAX_FRONTEND=OFF -DENABLE_OV_TF_FRONTEND=OFF \
  -DENABLE_OV_TF_LITE_FRONTEND=OFF -DENABLE_OV_GGUF_FRONTEND=OFF
cmake --build build-ncs2 --target openvino_ncs2_plugin pyopenvino --parallel 4
```

Для x86 host upstream также может потребовать подмодуль `thirdparty/xbyak`.
Для других включённых компонентов нужны их обычные upstream зависимости.
Извлечение `.blob` не требует XML frontend; отключённые CPU/GPU/frontends
в этом примере уменьшают состав, а не скрывают подмену устройства.

Для Buildroot передать его `CMAKE_TOOLCHAIN_FILE` и target sysroot.
Не подмешивать host libusb/OpenVINO или Python headers другой архитектуры.
Сборка и установка пакетов в существующий образ CM4 остаются у разработчика
образа; готового SD/eMMC image данный форк не содержит.
При компонентной установке обязательно установить и `core`, и `myriad`.

## Модель и USB firmware

В репозитории программы находится готовый комплект:
[buildroot/](https://github.com/dimaystinov/roki_next_generation/tree/main/buildroot).

- `ball.blob` → `/usr/share/roki/ball.blob`.
- `usb-ma2x8x.mvcmd` → `/usr/share/roki/firmware/usb-ma2x8x.mvcmd`.
- `NCS2_FIRMWARE_DIR=/usr/share/roki/firmware` в окружении приложения.

Там же записаны SHA256, происхождение firmware и исходной модели, а также
host C++-инструмент подготовки blob. Эти бинарники не дублируются в форке
OpenVINO. Firmware загружается в USB NCS2 при его открытии; это не firmware STM
и не образ носителя CM4. Правила доступа устройства до/после boot берутся из
[`97-myriad-usbboot.rules`](src/plugins/intel_myriad/thirdparty/mvnc/src/97-myriad-usbboot.rules)
и адаптируются к менеджеру устройств образа.

## Новый Python API

```python
import io
from pathlib import Path
import numpy as np
import openvino as ov

core = ov.Core()
print(core.get_versions('MYRIAD'))
print(core.get_property('MYRIAD', 'AVAILABLE_DEVICES'))
model = core.import_model(
    io.BytesIO(Path('/usr/share/roki/ball.blob').read_bytes()),
    'MYRIAD', {'NCS2_FIRMWARE_DIR': '/usr/share/roki/firmware'},
)
request = model.create_infer_request()
# Диагностика: для распознавания здесь нужен подготовленный кадр, не нули.
inputs = {i: np.zeros(port.shape, dtype=port.element_type.to_dtype())
          for i, port in enumerate(model.inputs)}
request.infer(inputs)
outputs = [request.get_output_tensor(i).data.copy()
           for i in range(len(model.outputs))]
```

При штатной установке повторный `register_plugin(..., 'MYRIAD')` не нужен.
Приватный тестовый плагин используется под отдельным именем, чтобы не
конкурировать с настоящей регистрацией MYRIAD.

Blob задаёт физический layout: если в нём NHWC, Python увидит NHWC.
Плагин не выполняет resize, RGB/BGR swap или нормализацию автоматически.
Готовый футбольный blob имеет U8 BGR `[1,640,640,3]` с preprocessing в графе;
Python Roki выполняет letterbox и YOLOv5 postprocessing.

## Отказы и испытания

Исключения плагина можно перехватить, но segfault/abort нативной библиотеки
нельзя надёжно локализовать Python `try/except` внутри того же процесса.
Поэтому Roki использует дочерний процесс на том же новом Python, общий буфер
BGR, таймаут ответа и цветовой fallback. Механизм расположен в приложении,
а не скрыт внутри OpenVINO. Неисправный USB SDK не должен вызываться каждым
следующим кадром: после отказа требуется явное восстановление сессии.

Тесты плагина включаются `-DENABLE_MYRIAD_NCS2_TESTS=ON`.
`NCS2_TEST_PYTHONPATH` должен указывать на каталог `python`, содержащий
**собранный здесь** пакет `openvino`, например `bin/arm64/Release/python`.
После сборки production/test plugin, `ncs2_blob_tests` и `pyopenvino`:

```sh
ctest --test-dir build-ncs2 -R ncs2 --output-on-failure
```

Проверяются parser/transfer, sync/async, несколько requests, соответствие
ответов, ошибки/таймауты и регистрация production plugin. Тестовый транспорт
не выполняет нейросеть и не доказывает работу физического NCS2.
На CM4 нужны USB boot, inference настоящей модели, проверка качества,
задержек, длительной работы и извлечения устройства во время матча.
Состояние аппаратной проверки: CM4/NCS2 в среде разработки отсутствует.

## Python wheel и проверенные результаты

`setup.py` дополнен компонентом `myriad`, поэтому production-плагин включается
в wheel. Fake USB library туда не устанавливается. На машине сборки с
подготовленными Python build-зависимостями можно включить упаковку:

```sh
python3 -m pip install -r src/bindings/python/wheel/requirements-dev.txt \
  -r src/bindings/python/requirements.txt
cmake -S . -B build-ncs2 -DENABLE_WHEEL=ON
cmake --build build-ncs2 --target ie_wheel --parallel 4
```

Результат находится в `build-ncs2/wheels/`. Проверить его состав:

```sh
python3 src/plugins/intel_myriad/tests/check_wheel.py /path/to/openvino.whl
```

На macOS arm64 для загрузки локально собранного runtime в Python нужно
`-DOV_FORCE_ADHOC_SIGN=ON`. Это настройка host-проверки, к Linux/CM4 она
не относится. libusb остаётся системной зависимостью; wheel не содержит
firmware или готовый образ робота.

Проверено 17 сентября 2026 на macOS arm64 / Python 3.14.3:

- Собраны runtime OpenVINO 2026.5.0, production и test plugins, Python bindings.
- Три CTest проходят: 25 некорректных вариантов blob, sync/async и несколько
  requests с имитацией USB, штатная регистрация production MYRIAD.
- Wheel собран, состав проверен, установлен в отдельное окружение; MYRIAD
  загружается из установленного пакета. Реальных устройств в среде нет (`[]`).
- Native plugin зависит от нового OpenVINO, libusb и системных библиотек;
  старой библиотеки OpenVINO среди зависимостей нет.
- Программа Roki использует как встроенную регистрацию, так и явный путь.
  Её дочерний процесс импортировал настоящую футбольную blob через новый
  runtime с тестовым транспортом. Это не аппаратное выполнение сети.
- Тесты приложения: 60 passed, 10 ожидаемых xfail известных дефектов локализации.

Сборка под конкретный Buildroot toolchain и inference на физическом NCS2
остаются задачами проверки образа. Этот форк не следует маркировать готовой
прошивкой или доказанным решением для матча до таких испытаний.
