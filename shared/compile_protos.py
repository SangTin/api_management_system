import os
import subprocess
import shutil

def compile_protos():
    """Biên dịch tất cả file .proto thành Python code"""
    # Thư mục chứa file .proto
    proto_dir = os.path.join(os.path.dirname(__file__), 'grpc', 'protos')
    
    # Thư mục đích cho mã được tạo
    output_dir = os.path.join(
        os.path.dirname(__file__), 
        'grpc', 
        'generated'
    )
    
    # Đảm bảo thư mục đích tồn tại và trống
    if os.path.exists(output_dir):
        # Xóa các file cũ nhưng giữ __init__.py
        for item in os.listdir(output_dir):
            if item != '__init__.py':
                item_path = os.path.join(output_dir, item)
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
    else:
        os.makedirs(output_dir)
        # Tạo __init__.py
        with open(os.path.join(output_dir, '__init__.py'), 'w') as f:
            f.write('# Generated Python code from .proto files\n')
    
    # Tìm tất cả file .proto
    proto_files = []
    for root, _, files in os.walk(proto_dir):
        for file in files:
            if file.endswith('.proto'):
                proto_files.append(os.path.join(root, file))
    
    # Biên dịch từng file .proto
    for proto_file in proto_files:
        print(f"Compiling {proto_file}...")
        try:
            # Gọi protoc để biên dịch
            subprocess.check_call([
                'python', '-m', 'grpc_tools.protoc',
                f'--proto_path={proto_dir}',
                f'--python_out={output_dir}',
                f'--grpc_python_out={output_dir}',
                proto_file
            ])
            print(f"Successfully compiled {proto_file}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to compile {proto_file}: {e}")
    
    print("Proto compilation completed")

def fix_grpc_imports(directory):
    """Fix imports in generated *_pb2_grpc.py files"""
    for filename in os.listdir(directory):
        if filename.endswith('_pb2_grpc.py'):
            filepath = os.path.join(directory, filename)
            
            # Đọc file
            with open(filepath, 'r') as file:
                content = file.read()
            
            # Tìm và thay thế import
            module_name = filename.replace('_pb2_grpc.py', '_pb2')
            pattern = f'import {module_name} as'
            replacement = f'from . import {module_name} as'
            
            new_content = content.replace(pattern, replacement)
            
            # Ghi nội dung mới
            with open(filepath, 'w') as file:
                file.write(new_content)
            
            print(f"Fixed imports in {filename}")

if __name__ == '__main__':
    compile_protos()
    fix_grpc_imports(os.path.join(os.path.dirname(__file__), 'grpc', 'generated'))