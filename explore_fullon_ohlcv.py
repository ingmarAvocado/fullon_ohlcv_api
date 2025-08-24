#!/usr/bin/env python3
"""
Explore fullon_ohlcv library interface to understand available classes, methods, and data models.
This will help us implement the REST API endpoints correctly.
"""

import inspect
import sys
from typing import Any, Dict, List

def explore_module(module_name: str) -> Dict[str, Any]:
    """Explore a module and return information about its contents."""
    try:
        module = __import__(module_name, fromlist=[''])
        
        info = {
            'module_name': module_name,
            'doc': getattr(module, '__doc__', None),
            'classes': {},
            'functions': {},
            'constants': {}
        }
        
        # Get all public attributes
        for name in dir(module):
            if name.startswith('_'):
                continue
                
            try:
                obj = getattr(module, name)
                
                if inspect.isclass(obj):
                    info['classes'][name] = {
                        'doc': inspect.getdoc(obj),
                        'methods': [],
                        'properties': []
                    }
                    
                    # Get class methods and properties
                    for method_name in dir(obj):
                        if method_name.startswith('_') and method_name != '__init__':
                            continue
                            
                        try:
                            method_obj = getattr(obj, method_name)
                            if inspect.ismethod(method_obj) or inspect.isfunction(method_obj):
                                try:
                                    sig = inspect.signature(method_obj)
                                    info['classes'][name]['methods'].append({
                                        'name': method_name,
                                        'signature': str(sig),
                                        'doc': inspect.getdoc(method_obj)
                                    })
                                except:
                                    info['classes'][name]['methods'].append({
                                        'name': method_name,
                                        'signature': 'Unable to get signature',
                                        'doc': inspect.getdoc(method_obj)
                                    })
                            elif isinstance(method_obj, property):
                                info['classes'][name]['properties'].append({
                                    'name': method_name,
                                    'doc': inspect.getdoc(method_obj)
                                })
                        except Exception as e:
                            print(f"Error exploring method {method_name}: {e}")
                            
                elif inspect.isfunction(obj):
                    try:
                        sig = inspect.signature(obj)
                        info['functions'][name] = {
                            'signature': str(sig),
                            'doc': inspect.getdoc(obj)
                        }
                    except:
                        info['functions'][name] = {
                            'signature': 'Unable to get signature',
                            'doc': inspect.getdoc(obj)
                        }
                else:
                    # Constants or other objects
                    info['constants'][name] = {
                        'type': type(obj).__name__,
                        'value': str(obj) if len(str(obj)) < 100 else f"{str(obj)[:97]}..."
                    }
                    
            except Exception as e:
                print(f"Error exploring {name}: {e}")
        
        return info
        
    except ImportError as e:
        return {'error': f"Could not import {module_name}: {e}"}
    except Exception as e:
        return {'error': f"Error exploring {module_name}: {e}"}

def print_module_info(info: Dict[str, Any]):
    """Print module information in a readable format."""
    if 'error' in info:
        print(f"❌ {info['error']}")
        return
        
    print(f"📦 Module: {info['module_name']}")
    if info['doc']:
        print(f"📖 Description: {info['doc']}")
    
    # Classes
    if info['classes']:
        print("\n🏗️ Classes:")
        for class_name, class_info in info['classes'].items():
            print(f"\n  📋 {class_name}")
            if class_info['doc']:
                print(f"     {class_info['doc']}")
            
            if class_info['methods']:
                print("     🔧 Methods:")
                for method in class_info['methods'][:10]:  # Limit to first 10
                    print(f"       • {method['name']}{method['signature']}")
                    if method['doc']:
                        print(f"         {method['doc'][:100]}...")
                
                if len(class_info['methods']) > 10:
                    print(f"       ... and {len(class_info['methods']) - 10} more methods")
            
            if class_info['properties']:
                print("     🔖 Properties:")
                for prop in class_info['properties']:
                    print(f"       • {prop['name']}")
                    if prop['doc']:
                        print(f"         {prop['doc'][:100]}...")
    
    # Functions
    if info['functions']:
        print("\n⚙️ Functions:")
        for func_name, func_info in info['functions'].items():
            print(f"  • {func_name}{func_info['signature']}")
            if func_info['doc']:
                print(f"    {func_info['doc'][:100]}...")
    
    # Constants
    if info['constants']:
        print("\n📌 Constants:")
        for const_name, const_info in info['constants'].items():
            print(f"  • {const_name}: {const_info['type']} = {const_info['value']}")

def main():
    """Main exploration function."""
    print("🔍 Exploring fullon_ohlcv library interface...")
    print("=" * 60)
    
    # Modules to explore
    modules_to_explore = [
        'fullon_ohlcv',
        'fullon_ohlcv.repositories',
        'fullon_ohlcv.models',
        'fullon_log'
    ]
    
    all_info = {}
    
    for module in modules_to_explore:
        print(f"\n{'='*60}")
        info = explore_module(module)
        all_info[module] = info
        print_module_info(info)
    
    return all_info

if __name__ == "__main__":
    main()