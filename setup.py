from setuptools import setup

setup(
    name='epythets',
    version='v0.0.7',
    python_requires='>=3.8.0',
    install_requires='pymorphy2',
    packages=['epythets'],
    url='https://github.com/strizhechenko/epythets',
    license='MIT',
    author='Oleg Strizhechenko',
    author_email='oleg.strizhechenko@gmail.com',
    description='С помощью pymorphy извлекаем из текстов множества эпитетов, нормализуем и сохраняем их в БД sqlite.',
    entry_points={
        "console_scripts": [
            "epythets = epythets.__init__:main"
        ],
    },
    long_description_content_type='text/markdown',
    long_description=open('README.md').read(),
)
