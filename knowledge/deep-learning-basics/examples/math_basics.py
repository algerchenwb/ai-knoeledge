"""独立教学示例：只使用 Python 标准库，不替代 PyTorch 集成验证。"""
import math

def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))] for i in range(len(a))]

a = [[1, 2], [3, 4]]
b = [[5, 6], [7, 8]]
elementwise = [[a[i][j] * b[i][j] for j in range(2)] for i in range(2)]
product = matmul(a, b)
assert elementwise == [[5, 12], [21, 32]]
assert product == [[19, 22], [43, 50]]
print("elementwise:", elementwise, "matmul:", product)

x, y, w, bias = 2.0, 5.0, 1.0, 0.0
def loss(weight):
    return (weight * x + bias - y) ** 2

error = w * x + bias - y
dw, db = 2 * error * x, 2 * error
h = 1e-5
numeric_dw = (loss(w + h) - loss(w - h)) / (2 * h)
assert math.isclose(dw, numeric_dw, rel_tol=1e-8)
new_w, new_b = w - 0.1 * dw, bias - 0.1 * db
new_loss = (new_w * x + new_b - y) ** 2
assert math.isclose(new_loss, 0.0, abs_tol=1e-12)
print("gradients:", dw, db, "finite_difference:", numeric_dw)
print("one_step:", new_w, new_b, "loss:", new_loss)

prob = 1 / (1 + math.exp(-2))
assert math.isclose(prob, 0.8807970779778823)
print("softmax([2,0]) first class:", prob)

# 手工推导平均平方误差的梯度，执行全批量梯度下降。
# 与文中的 PyTorch 微批训练不是逐步数值等价，仅核对学习机制。
xs = [-1 + i / 40 for i in range(81)]
ys = [2 * value + 1 for value in xs]
w, bias = 0.0, 0.0
initial_loss = sum(v * v for v in ys) / len(ys)
for _ in range(200):
    errors = [w * value + bias - target for value, target in zip(xs, ys)]
    dw = 2 * sum(e * value for e, value in zip(errors, xs)) / len(xs)
    db = 2 * sum(errors) / len(xs)
    w -= 0.1 * dw
    bias -= 0.1 * db

train_mse = sum((w*v+bias-t)**2 for v,t in zip(xs,ys)) / len(xs)
val_x = [-0.85, -0.25, 0.35, 0.95]
val_mse = sum((w*v+bias-(2*v+1))**2 for v in val_x) / len(val_x)
assert math.isclose(w, 2, abs_tol=1e-5)
assert math.isclose(bias, 1, abs_tol=1e-5)
assert train_mse < 1e-10 and val_mse < 1e-10
print("training:", initial_loss, "->", train_mse,
      "validation:", val_mse, "weight:", w, "bias:", bias)
