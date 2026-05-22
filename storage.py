#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""试卷管理系统 - 云存储模块"""

import os
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename

class StorageManager:
    """存储管理器，支持本地和云端存储"""
    
    def __init__(self, storage_type='local', upload_folder='uploads'):
        self.storage_type = storage_type
        self.upload_folder = os.path.abspath(upload_folder)
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def upload_file(self, file, filename=None, folder='exams'):
        """上传文件"""
        if filename is None:
            filename = file.filename or 'upload'
        
        # 生成唯一文件名
        ext = os.path.splitext(filename)[1].lower()
        if not ext:
            safe_name = secure_filename(filename)
            ext = os.path.splitext(safe_name)[1].lower()
        unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(filename.encode()).hexdigest()[:8]}{ext}"
        
        if self.storage_type == 'local':
            return self._upload_local(file, unique_name, folder)
        else:
            return self._upload_cloud(file, unique_name, folder)
    
    def _upload_local(self, file, filename, folder):
        """本地存储"""
        folder_path = os.path.join(self.upload_folder, folder)
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, filename)
        file.save(file_path)
        
        return {
            'success': True,
            'file_path': file_path,
            'file_name': filename,
            'url': f'/uploads/{folder}/{filename}'
        }
    
    def _upload_cloud(self, file, filename, folder):
        """云端存储"""
        from database import get_config
        
        cloud_provider = get_config('cloud_provider', '')
        
        if cloud_provider == '阿里云OSS':
            return self._upload_to_aliyun_oss(file, filename, folder)
        elif cloud_provider == '腾讯云COS':
            return self._upload_to_tencent_cos(file, filename, folder)
        elif cloud_provider == '七牛云':
            return self._upload_to_qiniu(file, filename, folder)
        elif cloud_provider == 'MinIO':
            return self._upload_to_minio(file, filename, folder)
        else:
            # 回退到本地存储
            return self._upload_local(file, filename, folder)
    
    def _upload_to_aliyun_oss(self, file, filename, folder):
        """上传到阿里云OSS"""
        try:
            import oss2
            from database import get_config
            
            endpoint = get_config('cloud_endpoint', '')
            access_key = get_config('cloud_access_key', '')
            secret_key = get_config('cloud_secret_key', '')
            bucket_name = get_config('cloud_bucket', '')
            
            auth = oss2.Auth(access_key, secret_key)
            bucket = oss2.Bucket(auth, endpoint, bucket_name)
            
            object_name = f'{folder}/{filename}'
            bucket.put_object(object_name, file)
            
            url = f'https://{bucket_name}.{endpoint}/{object_name}'
            
            return {
                'success': True,
                'file_path': object_name,
                'file_name': filename,
                'cloud_url': url,
                'url': url
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _upload_to_tencent_cos(self, file, filename, folder):
        """上传到腾讯云COS"""
        try:
            from qcloud_cos import CosConfig, CosS3Client
            from database import get_config
            
            secret_id = get_config('cloud_access_key', '')
            secret_key = get_config('cloud_secret_key', '')
            region = get_config('cloud_endpoint', 'ap-guangzhou')
            bucket = get_config('cloud_bucket', '')
            
            config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
            client = CosS3Client(config)
            
            object_name = f'{folder}/{filename}'
            client.upload_file(
                Bucket=bucket,
                Key=object_name,
                Body=file
            )
            
            url = f'https://{bucket}.cos.{region}.myqcloud.com/{object_name}'
            
            return {
                'success': True,
                'file_path': object_name,
                'file_name': filename,
                'cloud_url': url,
                'url': url
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _upload_to_qiniu(self, file, filename, folder):
        """上传到七牛云"""
        try:
            from qiniu import Auth, put_data
            from database import get_config
            
            access_key = get_config('cloud_access_key', '')
            secret_key = get_config('cloud_secret_key', '')
            bucket = get_config('cloud_bucket', '')
            
            q = Auth(access_key, secret_key)
            token = q.upload_token(bucket)
            
            object_name = f'{folder}/{filename}'
            ret, info = put_data(token, object_name, file.read())
            
            if info.status_code == 200:
                domain = get_config('cloud_endpoint', '')
                url = f'http://{domain}/{object_name}'
                return {
                    'success': True,
                    'file_path': object_name,
                    'file_name': filename,
                    'cloud_url': url,
                    'url': url
                }
            else:
                return {'success': False, 'error': f'上传失败: {info}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _upload_to_minio(self, file, filename, folder):
        """上传到MinIO"""
        try:
            from minio import Minio
            from database import get_config
            
            endpoint = get_config('cloud_endpoint', 'localhost:9000')
            access_key = get_config('cloud_access_key', '')
            secret_key = get_config('cloud_secret_key', '')
            bucket = get_config('cloud_bucket', '')
            secure = endpoint.startswith('https')
            
            client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
            
            # 确保bucket存在
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
            
            object_name = f'{folder}/{filename}'
            client.put_object(bucket, object_name, file, length=-1, part_size=10*1024*1024)
            
            protocol = 'https' if secure else 'http'
            url = f'{protocol}://{endpoint}/{bucket}/{object_name}'
            
            return {
                'success': True,
                'file_path': object_name,
                'file_name': filename,
                'cloud_url': url,
                'url': url
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_file(self, file_path, cloud_url=None):
        """删除文件"""
        if self.storage_type == 'local':
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                return True
            except:
                return False
        else:
            # 云端删除逻辑
            return True
    
    def get_file_url(self, file_path, cloud_url=None):
        """获取文件URL"""
        if cloud_url:
            return cloud_url
        if self.storage_type == 'local':
            return f'/uploads/{os.path.basename(file_path)}'
        return file_path


def get_storage_manager(upload_folder=None):
    """获取存储管理器实例"""
    from database import get_config
    
    storage_type = get_config('storage_type', 'local')
    return StorageManager(storage_type, upload_folder or 'uploads')


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}

def allowed_file(filename):
    """检查文件是否允许上传"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == '__main__':
    manager = StorageManager('local')
    print(f"存储管理器初始化完成: {manager.storage_type}")
