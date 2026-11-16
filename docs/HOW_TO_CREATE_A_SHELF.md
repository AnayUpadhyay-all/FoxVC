# How to Build a Shelf in FoxVC (10-Minute Tutorial)

In FoxVC, standard library modules are called **Shelves** (e.g. `shelf net`, `shelf db`, `shelf crypto`, `shelf file`, `shelf text`).

Writing a new shelf takes only **10–15 minutes**. This guide will walk you through building one from scratch.

---

### Step 1: Create Your Shelf File
In the `engine/shelves/` folder, create a new Python file:
`engine/shelves/my_shelf.py`

### Step 2: Write Your Shelf Functions
Here is a complete starter template for `engine/shelves/my_shelf.py`:

```python
"""
FoxVC MyShelf Module (shelf my_shelf)
Provides custom utilities to FoxVC scripts.
"""
from typing import Dict, Any, Optional
from engine.shelves.common import to_fox_val, _clean_obj, SecurityPolicy


def fox_hello(name: str = "World") -> str:
    """Returns a greeting string."""
    return f"Hello, {name} from FoxVC!"


def fox_add_ten(number: float) -> float:
    """Adds 10 to a number."""
    return float(number) + 10.0


def get_my_shelf(policy: Optional[SecurityPolicy] = None) -> Dict[str, Any]:
    """
    Returns the dictionary of functions exposed globally to FoxVC scripts.
    """
    return {
        "hello": fox_hello,
        "addTen": fox_add_ten,
    }
```

---

### Step 3: Register Your Shelf in `engine/shelves/__init__.py`
Open `engine/shelves/__init__.py` and add your shelf:

```python
from .my_shelf import get_my_shelf

# Inside get_all_shelves(policy=None):
shelves.update(get_my_shelf(policy))
```

---

### Step 4: Write a Quick Unit Test
Open `tests/test_v1_features.py` (or create `tests/test_my_shelf.py`):

```python
import unittest
from engine.runner import run_foxvc

class TestMyShelf(unittest.TestCase):
    def test_hello_function(self):
        code = """
msg = hello("Fox")
say msg
emit msg
"""
        res = run_foxvc(code, engine_mode="interp", as_result=False)
        self.assertEqual(res, "Hello, Fox from FoxVC!")

if __name__ == "__main__":
    unittest.main()
```

Run tests to verify:
```bash
python3 -m unittest tests/test_v1_features.py
```

---

### Step 5: Submit Your Pull Request!
1. Commit your new shelf:
   ```bash
   git add engine/shelves/my_shelf.py engine/shelves/__init__.py tests/
   git commit -m "feat(shelf): add my_shelf"
   ```
2. Open a Pull Request on GitHub at [https://github.com/AnayUpadhyay-all/FoxVC](https://github.com/AnayUpadhyay-all/FoxVC).
3. Your shelf will become an official part of the FoxVC language standard!
