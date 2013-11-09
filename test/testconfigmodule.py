#!/usr/bin/env python3

import unittest
import sys
import random

sys.path.append('../src')

from config import ConfigParameter
from config import ConfigDatabase
from config import CommandLineArgumentsLoader

class TestConfigureParameter(unittest.TestCase):
    def setUp(self):
        pass

    def test_import_config_module(self):
        self.assertIsNotNone(ConfigParameter)
        self.assertIsNotNone(ConfigDatabase)

    def test_init_param(self):
        p = ConfigParameter('test1')
        self.assertIsNotNone(p)

    def test_name(self):
        names = ['klb', '1ab', 's#a']
        for n in names:
            p = ConfigParameter(name = n)
            self.assertEqual(p.name, n)

    def test_invalid_name(self):
        names = ['k b', '\tab', 's\na']
        for n in names:
            with self.assertRaises(ValueError, msg="parameter name can't contain space"):
                ConfigParameter(name = n)

class TestConfigureDatabase(unittest.TestCase):
    def setUp(self):
        pass

    def test_prog(self):
        db = ConfigDatabase('test1')
        self.assertEqual(db.prog, 'test1')

    def test_desc(self):
        db = ConfigDatabase('test1', 'a test database')
        self.assertEqual(db.prog, 'test1')
        self.assertEqual(db.description,  'a test database')

    def test_parameter_init(self):
        params = [
                    ConfigParameter('123'), 
                    ConfigParameter('456')
                 ]
        db = ConfigDatabase('test1', parameters=params)
        self.assertListEqual(db.parameters, params)

    def test_repr(self):
        params = [
                    ConfigParameter('123', type=''), 
                    ConfigParameter('456', type='')
                 ]
        db = ConfigDatabase('test1', description='test desc', parameters=params)
        dbcopy = eval(repr(db))
        self.assertEqual(db.prog, dbcopy.prog)
        self.assertEqual(db.description, dbcopy.description)
        self.assertListEqual(db.parameters, dbcopy.parameters)

    def test_add_parameters(self):
        params = [
                    ConfigParameter('123'), 
                    ConfigParameter('456')
                 ]
        new_param = ConfigParameter('789')
        db = ConfigDatabase('test1', description='test desc', parameters=params)
        self.assertListEqual(db.parameters, params)
        db.add_param(new_param)
        self.assertListEqual(db.parameters, params+[new_param,])

    def test_no_dup_param(self):
        params = [
                    ConfigParameter('123', type=int), 
                    ConfigParameter('456', defaults=9)
                 ]
        new_param = ConfigParameter('123')
        db = ConfigDatabase('test1', description='test desc', parameters=params)
        self.assertListEqual(db.parameters, params)
        with self.assertRaises(NameError, msg='duplicated parameter name "%s" found'%(new_param.name,)):
            db.add_param(new_param)
        self.assertListEqual(db.parameters, params)


class TestCliLoader(unittest.TestCase):
    def getdb(self):
        return ConfigDatabase('test1', description='test desc')

    def getloader(self, generate_default=False):
        return CommandLineArgumentsLoader(generate_default=generate_default)

    def test_invalid_arg(self):
        loader = self.getloader()
        db = self.getdb()
        p = ConfigParameter(name='param1', type=int)
        db.add_param(p)
        with self.assertRaises(SystemExit) as se:
            loader.load(db, ['--not-exist'])
        self.assertEqual(se.exception.code, 2)

    def test_name(self):
        db = self.getdb()
        cli_opts = {'flags':['-p']}
        p = ConfigParameter(name='param1', type=lambda s:int(s,0), loader_opts={'cli':cli_opts})
        db.add_param(p)
        loader = self.getloader()

        with self.assertRaises(SystemExit) as se:
            loader.load(db, ['--param1', '1'])
        self.assertEqual(se.exception.code, 2)

        ans = loader.load(db, ['-p', '1'])
        self.assertEqual(getattr(ans, p.name), 1)

    def test_load_int(self):
        ds = [ 
                ('0', 0), 
                ('0x1aedead0b', 0x1aedead0b),
                ('0b0011', 3),
                ('-9571293', -9571293),
             ]

        db = self.getdb()
        p = ConfigParameter(name='param1', type=lambda s:int(s,0))
        db.add_param(p)
        loader = self.getloader()
        for s, d in ds:
            ans = loader.load(db, ['--param1', s])
            self.assertEqual(getattr(ans, p.name), d)
            
    def test_load_str(self):
        ds = [ 
                '    ',
                '#123',
                'as_',
                '9 9'
             ]

        db = self.getdb()
        p = ConfigParameter(name='param1')
        db.add_param(p)
        loader = self.getloader()
        for s in ds:
            ans = loader.load(db, ['--param1', s])
            self.assertEqual(getattr(ans, p.name), s)

    def test_load_choice(self):
        good = ['c1', 'c3', 'c2']
        choices = ('c0', 'c1', 'c2', 'c3')
        db = self.getdb()
        p = ConfigParameter(name='param1', defaults='c1', choices=choices)
        db.add_param(p)
        loader = self.getloader(generate_default=True)
        # try legal ones
        for s in good:
            ans = loader.load(db, ['--param1', s])
            self.assertEqual(getattr(ans, p.name), s)
        # test use default
        ans = loader.load(db, [])
        self.assertEqual(getattr(ans, p.name), good[0])

        # test illegal value
        with self.assertRaises(SystemExit) as se:
            loader.load(db, ['--param1', 'no-good'])
        self.assertEqual(se.exception.code, 2)
        

            
    def test_load_true(self):
        cli_opts = {'action':'store_true'}
        db = self.getdb()
        p = ConfigParameter(name='param1', loader_opts={'cli':cli_opts})
        db.add_param(p)
        loader = self.getloader()
        ans = loader.load(db, ['--param1'])
        self.assertTrue(getattr(ans, p.name))
        ans = loader.load(db, [])
        self.assertFalse(getattr(ans, p.name))

    def test_load_false(self):
        cli_opts = {'action':'store_false'}
        db = self.getdb()
        p = ConfigParameter(name='param1', loader_opts={'cli':cli_opts})
        db.add_param(p)
        loader = self.getloader()
        ans = loader.load(db, ['--param1'])
        self.assertFalse(getattr(ans, p.name))
        ans = loader.load(db, [])
        self.assertTrue(getattr(ans, p.name))

    def test_load_count(self):
        cli_opts = {'action':'count'}
        db = self.getdb()
        p = ConfigParameter(name='d', defaults=0, loader_opts={'cli':cli_opts})
        db.add_param(p)
        loader = self.getloader(generate_default=True)
        ans = loader.load(db, ['-d'])
        self.assertEqual(getattr(ans, p.name), 1)
        ans = loader.load(db, [])
        self.assertEqual(getattr(ans, p.name), 0)
        ans = loader.load(db, ['-d', '-d', '-d'])
        self.assertEqual(getattr(ans, p.name), 3)
        c = random.randint(0, 256)
        ans = loader.load(db, ['-'+'d'*c])
        self.assertEqual(getattr(ans, p.name), c)

    class TestDefaultValueLoader(unittest.TestCase):
        pass

