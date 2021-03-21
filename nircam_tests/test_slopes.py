import unittest
from astropy.io import fits, ascii
import numpy as np
import simple_slopes

class linefit_check(unittest.TestCase):

    def make_file(self):
        """ make a simulated im """
        Nx, Ny = 5, 3
        Ngroup = 3
        Tgroup= 10.0
        self.inputSlope = 3.3
        self.inputIntercept = 1.1
        
        A = np.zeros([Ny,Nx]) + self.inputIntercept
        B = np.ones([Ny,Nx]) * self.inputSlope
        Cube = np.zeros([Ngroup,Ny,Nx])
        for i in np.arange(Ngroup):
            Cube[i] = A + B * i * Tgroup
        primHDU = fits.PrimaryHDU(Cube)
        primHDU.header['NGROUP'] = Ngroup
        primHDU.header['TGROUP'] = Tgroup
        self.test_filename = 'nircam_tests/test_cube.fits'
        primHDU.writeto(self.test_filename,overwrite=True)
    
    def test_slope(self):
        self.make_file()
        primHDU = simple_slopes.fit_slope(self.test_filename)
        slopeFit = primHDU.data
        self.assertTrue(np.allclose(slopeFit,self.inputSlope))

    def test_intercept(self):
        self.make_file()
        primHDU = simple_slopes.fit_slope(self.test_filename,returnIntercept=True)
        interceptFit = primHDU.data
        self.assertTrue(np.allclose(interceptFit,self.inputIntercept))


class param_check(unittest.TestCase):
    def test_true_and_set(self):
        tmp = {'a': True, 'b': [5]}
        self.assertTrue(simple_slopes.exists_true(tmp,'a'))

    def test_not_in_dict(self):
        tmp = {'a': True, 'b': [5]}
        self.assertFalse(simple_slopes.exists_true(tmp,'c'))
    
    def test_false_and_set(self):
        tmp = {'a': False, 'b': [5]}
        self.assertFalse(simple_slopes.exists_true(tmp,'a'))

    def test_not_set_as_bool(self):
        tmp = {'a': True, 'b': [5]}
        self.assertFalse(simple_slopes.exists_true(tmp,'b'))
        

if __name__ == '__main__':
    unittest.main()
