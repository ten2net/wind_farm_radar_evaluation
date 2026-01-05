import streamlit as st
import numpy as np
import plotly.express as px
import pandas as pd

# 页面配置
st.set_page_config(
    page_title="NumPy 与 Streamlit 集成",
    page_icon="📊",
    layout="wide"
)

# 标题
st.title("📈 NumPy 在 Streamlit 中的应用")

# 创建侧边栏用于控制参数
with st.sidebar:
    st.header("📊 数据参数")
    
    # 数据大小控制
    array_size = st.slider(
        "数组大小", 
        min_value=10, 
        max_value=1000, 
        value=100,
        help="控制生成数据的大小"
    )
    
    # 随机种子
    seed = st.number_input("随机种子", value=42)
    np.random.seed(seed)
    
    # 数据类型选择
    data_type = st.selectbox(
        "数据类型",
        ["随机数", "正弦波", "正态分布", "线性空间"]
    )

# 主界面
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 数据生成", 
    "📊 数据分析", 
    "🔢 矩阵运算", 
    "🎨 可视化"
])

with tab1:
    st.header("NumPy 数据生成")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1D 数组示例")
        
        # 根据选择生成不同数据
        if data_type == "随机数":
            data_1d = np.random.random(array_size)
        elif data_type == "正弦波":
            data_1d = np.sin(np.linspace(0, 4*np.pi, array_size))
        elif data_type == "正态分布":
            data_1d = np.random.normal(0, 1, array_size)
        else:  # 线性空间
            data_1d = np.linspace(0, 10, array_size)
        
        # 显示数据
        st.write(f"**数据形状:** {data_1d.shape}")
        st.write(f"**数据类型:** {data_1d.dtype}")
        st.write(f"**统计信息:**")
        st.write({
            "平均值": f"{data_1d.mean():.4f}",
            "标准差": f"{data_1d.std():.4f}",
            "最小值": f"{data_1d.min():.4f}",
            "最大值": f"{data_1d.max():.4f}"
        })
        
        # 显示前10个数据
        st.write("**前10个数据点:**")
        st.dataframe(data_1d[:10].reshape(-1, 1), height=200)
    
    with col2:
        st.subheader("2D 数组示例")
        
        # 生成2D数据
        rows = st.slider("行数", 2, 20, 5)
        cols = st.slider("列数", 2, 20, 5)
        
        data_2d = np.random.randn(rows, cols)
        
        # 显示2D数据
        st.write(f"**矩阵形状:** {data_2d.shape}")
        st.write("**矩阵值:**")
        st.dataframe(data_2d, width='stretch')
        
        # 矩阵基本信息
        st.write("**矩阵信息:**")
        st.write({
            "行列式": f"{np.linalg.det(data_2d):.4f}" if rows == cols else "非方阵",
            "秩": np.linalg.matrix_rank(data_2d),
            "迹": f"{np.trace(data_2d):.4f}" if rows == cols else "非方阵"
        })

with tab2:
    st.header("NumPy 数据分析")
    
    # 创建示例数据集
    st.subheader("示例数据集")
    
    # 生成多种类型的数组
    uniform_data = np.random.uniform(-5, 5, 1000)
    normal_data = np.random.normal(0, 2, 1000)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**均匀分布数据统计:**")
        st.json({
            "计数": len(uniform_data),
            "平均值": float(uniform_data.mean()),
            "中位数": float(np.median(uniform_data)),
            "标准差": float(uniform_data.std()),
            "方差": float(uniform_data.var()),
            "范围": f"[{uniform_data.min():.2f}, {uniform_data.max():.2f}]",
            "四分位距": f"{np.percentile(uniform_data, 75) - np.percentile(uniform_data, 25):.2f}"
        })
        
        # 直方图
        st.subheader("均匀分布直方图")
        hist, bins = np.histogram(uniform_data, bins=20)
        chart_data = pd.DataFrame({
            "区间起始": bins[:-1],
            "区间结束": bins[1:],
            "频数": hist
        })
        st.bar_chart(chart_data.set_index("区间起始")["频数"])
    
    with col2:
        st.write("**正态分布数据统计:**")
        st.json({
            "计数": len(normal_data),
            "偏度": float(pd.Series(normal_data).skew()),
            "峰度": float(pd.Series(normal_data).kurtosis()),
            "25% 分位数": float(np.percentile(normal_data, 25)),
            "50% 分位数": float(np.percentile(normal_data, 50)),
            "75% 分位数": float(np.percentile(normal_data, 75))
        })
        
        # 箱线图
        st.subheader("正态分布箱线图")
        fig = px.box(y=normal_data, title="正态分布数据")
        st.plotly_chart(fig, width='stretch')

with tab3:
    st.header("NumPy 矩阵运算")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("矩阵运算")
        
        # 创建矩阵
        matrix_a = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        matrix_b = np.array([[9, 8, 7], [6, 5, 4], [3, 2, 1]])
        
        st.write("**矩阵 A:**")
        st.dataframe(matrix_a)
        
        st.write("**矩阵 B:**")
        st.dataframe(matrix_b)
        
        # 矩阵运算
        operation = st.selectbox(
            "选择矩阵运算",
            ["加法", "减法", "乘法", "点积", "转置", "逆矩阵"]
        )
        
        if operation == "加法":
            result = matrix_a + matrix_b
            st.write("**A + B:**")
        elif operation == "减法":
            result = matrix_a - matrix_b
            st.write("**A - B:**")
        elif operation == "乘法":
            result = matrix_a * matrix_b
            st.write("**A * B (逐元素乘法):**")
        elif operation == "点积":
            result = np.dot(matrix_a, matrix_b)
            st.write("**A · B (矩阵乘法):**")
        elif operation == "转置":
            result = matrix_a.T
            st.write("**Aᵀ (A的转置):**")
        elif operation == "逆矩阵":
            try:
                result = np.linalg.inv(matrix_a)
                st.write("**A⁻¹ (A的逆矩阵):**")
            except np.linalg.LinAlgError:
                st.error("矩阵不可逆")
                result = None
        
        if result is not None:
            st.dataframe(result)
            
            # 显示矩阵属性
            st.write("**矩阵属性:**")
            st.write(f"形状: {result.shape}")
            st.write(f"秩: {np.linalg.matrix_rank(result)}")
            if result.shape[0] == result.shape[1]:  # 方阵
                st.write(f"行列式: {np.linalg.det(result):.4f}")
    
    with col2:
        st.subheader("线性代数运算")
        
        # 解线性方程组
        st.write("**解线性方程组:**")
        st.latex(r"""
        \begin{cases}
        2x + 3y = 8 \\
        5x - 2y = 1
        \end{cases}
        """)
        
        A = np.array([[2, 3], [5, -2]])
        b = np.array([8, 1])
        
        try:
            solution = np.linalg.solve(A, b)
            st.write(f"**解:** x = {solution[0]:.2f}, y = {solution[1]:.2f}")
        except np.linalg.LinAlgError:
            st.error("方程组无解")
        
        # 特征值和特征向量
        st.write("**特征值与特征向量:**")
        eigenvalues, eigenvectors = np.linalg.eig(matrix_a)
        
        st.write("**特征值:**")
        for i, val in enumerate(eigenvalues):
            st.write(f"λ{i+1} = {val:.4f}")
        
        st.write("**特征向量:**")
        st.dataframe(pd.DataFrame(eigenvectors, 
                                 columns=[f'λ{i+1}' for i in range(len(eigenvalues))]))

with tab4:
    st.header("NumPy 数据可视化")
    
    # 创建三维数据
    st.subheader("3D 数据可视化")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 生成3D数据
        x = np.linspace(-5, 5, 50)
        y = np.linspace(-5, 5, 50)
        X, Y = np.meshgrid(x, y)
        
        # 选择函数
        function_type = st.selectbox(
            "选择3D函数",
            ["正弦波", "高斯函数", "马鞍面", "锥面"]
        )
        
        if function_type == "正弦波":
            Z = np.sin(np.sqrt(X**2 + Y**2))
            title = "z = sin(√(x² + y²))"
        elif function_type == "高斯函数":
            Z = np.exp(-(X**2 + Y**2) / 10)
            title = "z = exp(-(x² + y²)/10)"
        elif function_type == "马鞍面":
            Z = X**2 - Y**2
            title = "z = x² - y²"
        else:  # 锥面
            Z = np.sqrt(X**2 + Y**2)
            title = "z = √(x² + y²)"
        
        # 使用plotly创建3D图
        import plotly.graph_objects as go
        
        fig = go.Figure(data=[
            go.Surface(
                z=Z, 
                x=X, 
                y=Y,
                colorscale='Viridis',
                contours={
                    "z": {"show": True, "usecolormap": True}
                }
            )
        ])
        
        fig.update_layout(
            title=title,
            scene=dict(
                xaxis_title="X",
                yaxis_title="Y",
                zaxis_title="Z",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            width=700,
            height=500
        )
        
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.subheader("可视化参数")
        
        resolution = st.slider("分辨率", 20, 100, 50)
        
        st.write("**数据统计:**")
        st.write({
            "最小值": f"{Z.min():.3f}",
            "最大值": f"{Z.max():.3f}",
            "平均值": f"{Z.mean():.3f}",
            "标准差": f"{Z.std():.3f}"
        })
        
        # 颜色映射选择
        colorscale = st.selectbox(
            "颜色映射",
            ["Viridis", "Plasma", "Jet", "Rainbow", "Hot"]
        )
        
        st.info(f"显示 {resolution}×{resolution} 个数据点")

# 在页面底部添加 NumPy 信息
with st.expander("ℹ️ NumPy 配置信息"):
    st.write("**NumPy 配置:**")
    st.json({
        "版本": np.__version__,
        "安装路径": np.__file__,
        "BLAS 信息": np.__config__.get_info('blas_opt_info'),
        "LAPACK 信息": np.__config__.get_info('lapack_opt_info')
    })
    
    st.write("**NumPy 功能支持:**")
    st.write({
        "复数支持": np.complex128 in np.sctypeDict.values(),
        "FFT 支持": hasattr(np.fft, 'fft'),
        "线性代数": hasattr(np, 'linalg'),
        "随机数生成": hasattr(np.random, 'default_rng')
    })

# 添加页脚
st.markdown("---")
st.markdown("### 🎯 NumPy 在 Streamlit 中的最佳实践")
st.info("""
1. **性能优化**: 使用向量化操作替代循环
2. **内存管理**: 注意大数组的内存使用
3. **数据类型**: 使用合适的 dtype 节省内存
4. **广播机制**: 利用 NumPy 广播提高效率
5. **随机种子**: 设置随机种子保证结果可重复
""")