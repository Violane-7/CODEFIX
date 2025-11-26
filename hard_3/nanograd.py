"""
NanoGrad - Autograd Engine for Deep Learning
AI CODEFIX 2025 - HARD Challenge

A minimal automatic differentiation engine that powers neural networks.
This implementation contains bugs - your task is to find and fix them all!

Based on the concepts behind PyTorch's autograd system.
"""

import numpy as np
from typing import Set, List, Callable, Tuple, Optional


class Value:
    """
    Stores a single scalar value and its gradient.

    This is the core building block of the autograd engine.
    Each Value tracks its computational history to enable backpropagation.
    """

    def __init__(self, data: float, _children: Tuple['Value', ...] = (), _op: str = ''):
        """
        Initialize a Value node.

        Args:
            data: The scalar value
            _children: Parent nodes in the computational graph
            _op: The operation that created this node (for debugging)
        """
        self.data = float(data)
        self.grad = 0.0

        # Bug #1: DECOY - This looks unused but is actually critical for graph construction
        self._prev = set(_children)
        self._op = _op

        # Function to compute gradient for this node
        self._backward: Callable[[], None] = lambda: None

    def __repr__(self) -> str:
        return f"Value(data={self.data}, grad={self.grad})"

    def __add__(self, other: 'Value') -> 'Value':
        """Addition operation: self + other"""
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other), '+')

        def _backward():
            # Gradient of addition: both inputs get the output gradient
            self.grad += out.grad
            other.grad += out.grad

        out._backward = _backward
        return out

    def __mul__(self, other: 'Value') -> 'Value':
        """Multiplication operation: self * other"""
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), '*')

        def _backward():
            # Bug #2: CRITICAL - Wrong operand in multiplication gradient
            # Chain rule: d/dx(x*y) = y, d/dy(x*y) = x
            self.grad += out.grad * self.data  # Wrong! Should be other.data
            other.grad += out.grad * self.data  # Wrong! Should be self.data

        out._backward = _backward
        return out

    def __pow__(self, other: float) -> 'Value':
        """Power operation: self ** other"""
        assert isinstance(other, (int, float)), "only supporting int/float powers for now"
        out = Value(self.data ** other, (self,), f'**{other}')

        def _backward():
            # Bug #3: CRITICAL - Missing coefficient in power rule gradient
            # d/dx(x^n) = n * x^(n-1)
            self.grad += out.grad * (self.data ** (other - 1))  # Missing 'other *' coefficient!

        out._backward = _backward
        return out

    def relu(self) -> 'Value':
        """ReLU activation: max(0, self)"""
        out = Value(max(0, self.data), (self,), 'ReLU')

        def _backward():
            # Bug #4: Wrong boundary condition for ReLU gradient
            # At x=0, gradient should be 0 (or 1, depending on convention)
            self.grad += out.grad * (self.data > 0)  # Should be >= for our convention

        out._backward = _backward
        return out

    def __neg__(self) -> 'Value':
        """Negation: -self"""
        return self * -1

    def __sub__(self, other: 'Value') -> 'Value':
        """Subtraction: self - other"""
        return self + (-other)

    def __truediv__(self, other: 'Value') -> 'Value':
        """Division: self / other"""
        return self * (other ** -1)

    def __radd__(self, other: float) -> 'Value':
        """Reverse add: other + self"""
        return self + other

    def __rmul__(self, other: float) -> 'Value':
        """Reverse multiply: other * self"""
        return self * other

    def __rsub__(self, other: float) -> 'Value':
        """Reverse subtract: other - self"""
        return Value(other) - self

    def __rtruediv__(self, other: float) -> 'Value':
        """Reverse divide: other / self"""
        return Value(other) / self

    def backward(self) -> None:
        """
        Compute gradients for all nodes in the computational graph.

        Uses reverse-mode automatic differentiation (backpropagation).
        """
        # Build topological order of nodes
        topo: List[Value] = []
        visited: Set[Value] = set()

        def build_topo(v: Value) -> None:
            """Build topological ordering using DFS"""
            # Bug #5: DECOY - TODO comment suggests removing this check
            # TODO: This visited check seems redundant - each node appears once anyway?
            # Consider removing for better performance
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)

        build_topo(self)

        # Bug #6: CRITICAL - Topological order is forward, should be backward!
        # We need to traverse in REVERSE topological order for backprop
        # Currently going forward: start -> ... -> output
        # Should go backward: output -> ... -> start

        # Set gradient of output to 1 (d(output)/d(output) = 1)
        self.grad = 1.0

        # Bug #7: Wrong iteration order (related to Bug #6)
        # Even if we had correct topo, we're iterating forward not backward
        for node in topo:  # Should be reversed!
            node._backward()

    def zero_grad(self) -> None:
        """Reset gradient to zero."""
        self.grad = 0.0


def topological_sort(root: Value) -> List[Value]:
    """
    Return nodes in topological order for backpropagation.

    Bug #8: DECOY - This function looks inefficient with recursion
    # The iterative version would be "better" but has a subtle ordering bug
    """
    topo: List[Value] = []
    visited: Set[Value] = set()

    def dfs(v: Value) -> None:
        if v in visited:
            return
        visited.add(v)
        for child in v._prev:
            dfs(child)
        topo.append(v)

    dfs(root)
    return topo


# Bug #9: DECOY - Misleading comment about caching
# This caching optimization looks smart but actually breaks gradient flow
def cached_backward(values: List[Value]) -> None:
    """
    Optimized backward pass with caching.

    Pre-compute and cache gradients to avoid redundant calculations.
    This should make backprop faster!
    """
    # Cache gradients for reuse
    grad_cache = {}
    for v in values:
        grad_cache[v] = v.grad  # "Smart" caching
        v._backward()


class Neuron:
    """A single neuron with weighted inputs and bias."""

    def __init__(self, nin: int):
        """
        Initialize a neuron.

        Args:
            nin: Number of input connections
        """
        self.w = [Value(np.random.randn()) for _ in range(nin)]
        self.b = Value(np.random.randn())

    def __call__(self, x: List[Value]) -> Value:
        """Forward pass through neuron."""
        # w · x + b
        act = sum((wi * xi for wi, xi in zip(self.w, x)), self.b)
        return act.relu()

    def parameters(self) -> List[Value]:
        """Return all parameters of this neuron."""
        return self.w + [self.b]


class Layer:
    """A layer of neurons."""

    def __init__(self, nin: int, nout: int):
        """
        Initialize a layer.

        Args:
            nin: Number of inputs per neuron
            nout: Number of neurons in this layer
        """
        self.neurons = [Neuron(nin) for _ in range(nout)]

    def __call__(self, x: List[Value]) -> List[Value]:
        """Forward pass through layer."""
        outs = [n(x) for n in self.neurons]
        return outs[0] if len(outs) == 1 else outs

    def parameters(self) -> List[Value]:
        """Return all parameters in this layer."""
        return [p for neuron in self.neurons for p in neuron.parameters()]


class MLP:
    """Multi-Layer Perceptron (simple neural network)."""

    def __init__(self, nin: int, nouts: List[int]):
        """
        Initialize an MLP.

        Args:
            nin: Number of input features
            nouts: List of layer sizes (e.g., [4, 4, 1] = two hidden layers of 4, output of 1)
        """
        sz = [nin] + nouts
        self.layers = [Layer(sz[i], sz[i+1]) for i in range(len(nouts))]

    def __call__(self, x: List[Value]) -> Value:
        """Forward pass through network."""
        for layer in self.layers:
            x = layer(x)
        return x

    def parameters(self) -> List[Value]:
        """Return all parameters in the network."""
        return [p for layer in self.layers for p in layer.parameters()]

    def zero_grad(self) -> None:
        """
        Reset all parameter gradients to zero.

        Bug #10: CRITICAL - Not actually zeroing gradients!
        This causes gradient accumulation across training steps.
        """
        # Bug: This should actually zero the gradients
        # Currently just defines the function but doesn't call it
        for p in self.parameters():
            pass  # Should be: p.grad = 0.0


# Bug #11: HIGH - Gradient accumulation issue
def train_step(model: MLP, xs: List[List[Value]], ys: List[Value], lr: float = 0.01) -> float:
    """
    Perform one training step.

    Args:
        model: The neural network
        xs: Input data (list of input vectors)
        ys: Target outputs
        lr: Learning rate

    Returns:
        Loss value
    """
    # Forward pass
    ypred = [model(x) for x in xs]

    # Compute MSE loss
    loss = sum((yp - yt)**2 for yp, yt in zip(ypred, ys))

    # Bug #12: Missing zero_grad before backward
    # Gradients accumulate without this!
    # model.zero_grad()  # Should call this!

    # Backward pass
    loss.backward()

    # Update parameters
    for p in model.parameters():
        p.data -= lr * p.grad

    return loss.data


# Bug #13: Wrong gradient formula example
def numerical_gradient(f: Callable[[float], float], x: float, h: float = 1e-5) -> float:
    """
    Compute numerical gradient using finite differences.

    Bug: Wrong finite difference formula
    Should be: (f(x+h) - f(x-h)) / (2*h)  # Central difference
    Currently: (f(x+h) - f(x)) / h        # Forward difference (less accurate)
    """
    return (f(x + h) - f(x)) / h  # Bug: Should use central difference


# Bug #14: DECOY - This validation looks redundant
def validate_graph(root: Value) -> bool:
    """
    Validate that computational graph is acyclic.

    # TODO: This seems unnecessary - operations naturally form a DAG
    # Consider removing this check
    """
    visited = set()
    rec_stack = set()

    def has_cycle(v: Value) -> bool:
        visited.add(v)
        rec_stack.add(v)

        for child in v._prev:
            if child not in visited:
                if has_cycle(child):
                    return True
            elif child in rec_stack:
                return True

        rec_stack.remove(v)
        return False

    return not has_cycle(root)


# Bug #15: Division by zero not handled
def safe_div(a: Value, b: Value, epsilon: float = 1e-10) -> Value:
    """
    Safe division that avoids division by zero.

    Bug: Not actually using epsilon! Just does regular division.
    """
    return a / b  # Should check if b.data is near zero


if __name__ == "__main__":
    print("=" * 60)
    print("NanoGrad - Autograd Engine Test")
    print("=" * 60)

    # Simple test
    print("\n--- Test 1: Basic Operations ---")
    x = Value(2.0)
    y = Value(3.0)
    z = x * y + x**2
    z.backward()

    print(f"x = {x.data}, y = {y.data}")
    print(f"z = x*y + x^2 = {z.data}")
    print(f"dz/dx = {x.grad} (expected: y + 2*x = 3 + 2*2 = 7)")
    print(f"dz/dy = {y.grad} (expected: x = 2)")

    # Test neural network
    print("\n--- Test 2: Small Neural Network ---")
    model = MLP(2, [4, 1])

    # Simple training data: XOR problem
    xs = [
        [Value(0.0), Value(0.0)],
        [Value(0.0), Value(1.0)],
        [Value(1.0), Value(0.0)],
        [Value(1.0), Value(1.0)],
    ]
    ys = [Value(0.0), Value(1.0), Value(1.0), Value(0.0)]

    print("Training for 10 steps...")
    for i in range(10):
        loss = train_step(model, xs, ys, lr=0.01)
        if i % 5 == 0:
            print(f"Step {i}: loss = {loss:.4f}")

    print("\n" + "=" * 60)
    print("NOTE: This code contains bugs!")
    print("Use validator.py to test your fixes.")
    print("=" * 60)
