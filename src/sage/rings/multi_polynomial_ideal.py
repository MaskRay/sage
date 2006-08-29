"""
Ideals in multivariate polynomial rings.

AUTHOR:
    -- William Stein
    -- Kiran S. Kedlaya (2006-02-12): added Macaulay2 analogues of
              some Singular features
    -- Martin Albrecht (2006-08-28): reorganized class hierarchy

EXAMPLES:
    sage: x,y,z = QQ['x,y,z'].gens()
    sage: I = ideal(x^5 + y^4 + z^3 - 1,  x^3 + y^3 + z^2 - 1)
    sage: B = I.groebner_basis()
    sage: len(B)
    3
    sage: [f in I for f in I.gens()]
    [True, True]

    sage: f = I.gens()[0]
    sage: I.reduce(f)
    0

    sage: g = I.gens()[1]
    sage: I.reduce(g)
    0

    sage: I.reduce(g+x^2)
    x^2

We compute a Groebner basis for cyclic 6, which is a standard
benchmark and test ideal.

    sage: R.<x,y,z,t,u,v> = QQ['x,y,z,t,u,v']
    sage: I = sage.rings.ideal.Cyclic(R,6)
    sage: B = I.groebner_basis()
    sage: len(B)
    45
"""

#*****************************************************************************
#
#   SAGE: System for Algebra and Geometry Experimentation
#
#       Copyright (C) 2005 William Stein <wstein@ucsd.edu>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#
#    This code is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    General Public License for more details.
#
#  The full text of the GPL is available at:
#
#                  http://www.gnu.org/licenses/
#*****************************************************************************

from ideal import Ideal_generic
from sage.interfaces.all import singular as singular_default, is_SingularElement
from sage.interfaces.all import macaulay2 as macaulay2_default
from sage.interfaces.all import is_SingularElement
singular = singular_default
from integer import Integer
from sage.structure.sequence import Sequence
from sage.misc.sage_eval import sage_eval

def is_MPolynomialIdeal(x):
    return isinstance(x, MPolynomialIdeal)


class MPolynomialIdeal_singular_repr:
    """
    An ideal in a multivariate polynomial ring, which has an
    underlying Singular ring associated to it.
    """
    def _cmp_(self, other):
        # Groebner basis determine equality since ideals are in the
        # same ring with same term order
        # TODO: This is wrong, it has to be the reduced GB (malb)

        #c = cmp(self.gens(), other.gens())
        #if c == 0:
        #    return c
        return cmp(self.groebner_basis(), other.groebner_basis())

    def _singular_(self, singular=None):
        """
        Return Singular ideal corresponding to this ideal.

        EXAMPLES:
            sage: R, (x,y) = PolynomialRing(QQ, 2, 'xy').objgens()
            sage: I = R.ideal([x^3 + y, y])
            sage: S = I._singular_()
            sage: S
            y,
            x^3+y
        """
        if singular is None: singular = singular_default
        try:
            self.ring()._singular_(singular).set_ring()
            I = self.__singular
            if not (I.parent() is singular):
                raise ValueError
            I._check_valid()
            return I
        except (AttributeError, ValueError):
            self.ring()._singular_(singular).set_ring()
            gens = [str(x) for x in self.gens()]
            if len(gens) == 0:
                gens = ['0']
            self.__singular = singular.ideal(gens)
        return self.__singular

    def _contains_(self, f):
        """
        EXAMPLES:
            sage: R, (x,y) = PolynomialRing(QQ, 2, 'xy').objgens()
            sage: I = (x^3 + y, y)*R
            sage: x in I
            False
            sage: y in I
            True
            sage: x^3 + 2*y in I
            True
        """
        S = singular_default
        f = S(f)
        I = self._singular_(S).std()
        g = f.reduce(I, 1)  # 1 avoids tail reduction (page 67 of singular book)
        return g.is_zero()

    def plot(self):
        """
        If you somehow manage to install surf, perhaps you can use
        this function to implicitly plot the real zero locus of this
        ideal (if principal).

        INPUT:
            self -- must be a principal ideal in 2 or 3 vars over QQ.

        EXAMPLES:
        Implicit plotting in 2-d:
            sage: R, (x,y) = MPolynomialRing(QQ,2).objgens()
            sage: I = R.ideal([y^3 - x^2])
            sage.: I.plot()        # cusp         (optional surf)
            sage: I = R.ideal([y^2 - x^2 - 1])
            sage.: I.plot()        # hyperbola    (optional surf)
            sage: I = R.ideal([y^2 + x^2*(1/4) - 1])
            sage.: I.plot()        # ellipse      (optional surf)
            sage: I = R.ideal([y^2-(x^2-1)*(x-2)])
            sage.: I.plot()        # elliptic curve  (optional surf)

        Implicit plotting in 3-d:
            sage: R, (x,y,z) = MPolynomialRing(QQ,3).objgens()
            sage: I = R.ideal([y^2 + x^2*(1/4) - z])
            sage.: I.plot()          # a cone         (optional surf)
            sage: I = R.ideal([y^2 + z^2*(1/4) - x])
            sage.: I.plot()          # same code, from a different angle  (optional surf)
            sage: I = R.ideal([x^2*y^2+x^2*z^2+y^2*z^2-16*x*y*z])
            sage.: I.plot()          # Steiner surface   (optional surf)

        AUTHOR:
            -- David Joyner (2006-02-12)
        """
        if self.ring().characteristic() != 0:
            raise TypeError, "base ring must have characteristic 0"
        if not self.is_principal():
            raise TypeError, "self must be principal"
        singular.lib('surf')
        I = singular(self)
        I.plot()

    def complete_primary_decomposition(self, algorithm="sy"):
        r"""
        INPUT:
            algorithm -- string:
                    'sy' -- (default) use the shimoyama-yokoyama algorithm
                    'gtz' -- use the gianni-trager-zacharias algorithm
        OUTPUT:
            list -- a list of primary ideals and their associated
                    primes
                        [(primary ideal, associated prime), ...]

        ALGORITHM: Uses Singular.

        EXAMPLES:
            sage: R, (x,y,z) = PolynomialRing(QQ, 3, 'xyz', order='lex').objgens()
            sage: p = z^2 + 1; q = z^3 + 2
            sage: I = (p*q^2, y-z^2)*R
            sage: pd = I.complete_primary_decomposition(); pd
            [(Ideal (1 + z^2, 1 + y) of Polynomial Ring in x, y, z over Rational Field, Ideal (1 + z^2, 1 + y) of Polynomial Ring in x, y, z over Rational Field), (Ideal (4 + 4*z^3 + z^6, -1*z^2 + y) of Polynomial Ring in x, y, z over Rational Field, Ideal (2 + z^3, -1*z^2 + y) of Polynomial Ring in x, y, z over Rational Field)]

            sage: I.complete_primary_decomposition(algorithm = 'gtz')
            [(Ideal (1 + z^2, -1*z^2 + y) of Polynomial Ring in x, y, z over Rational Field, Ideal (1 + z^2, -1*z^2 + y) of Polynomial Ring in x, y, z over Rational Field), (Ideal (4 + 4*z^3 + z^6, -1*z^2 + y) of Polynomial Ring in x, y, z over Rational Field, Ideal (2 + z^3, -1*z^2 + y) of Polynomial Ring in x, y, z over Rational Field)]
        """
        try:
            return self.__complete_primary_decomposition[algorithm]
        except AttributeError:
            self.__complete_primary_decomposition = {}
        except KeyError:
            pass
        I = self._singular_()
        I.parent().lib('primdec.lib')
        if algorithm == 'sy':
            P = I.primdecSY()
        elif algorithm == 'gtz':
            P = I.primdecGTZ()

        R = self.ring()
        V = [(R.ideal(X[1]), R.ideal(X[2])) for X in P]
        V = Sequence(V)
        self.__complete_primary_decomposition[algorithm] = V
        return self.__complete_primary_decomposition[algorithm]

    def primary_decomposition(self, algorithm='sy'):
        """
        EXAMPLES:
            sage: R, (x,y,z) = PolynomialRing(QQ, 3, 'xyz', order='lex').objgens()
            sage: p = z^2 + 1; q = z^3 + 2
            sage: I = (p*q^2, y-z^2)*R
            sage: I.primary_decomposition()   # this fails on some 64-bit machines sometimes during automated testing; I don't know why!
            [Ideal (1 + z^2, 1 + y) of Polynomial Ring in x, y, z over Rational Field, Ideal (4 + 4*z^3 + z^6, -1*z^2 + y) of Polynomial Ring in x, y, z over Rational Field]

        """
        return [I for I, _ in self.complete_primary_decomposition(algorithm)]

    def associated_primes(self, algorithm='sy'):
        """
        EXAMPLES:
            sage: R, (x,y,z) = PolynomialRing(QQ, 3, 'xyz').objgens()
            sage: p = z^2 + 1; q = z^3 + 2
            sage: I = (p*q^2, y-z^2)*R
            sage: I.associated_primes()
            [Ideal (1 + y, 1 + z^2) of Polynomial Ring in x, y, z over Rational Field, Ideal (z^2 - y, 2 + y*z, 2*z + y^2) of Polynomial Ring in x, y, z over Rational Field]
        """
        return [P for _,P in self.complete_primary_decomposition(algorithm)]

    def dimension(self):
        """
        The dimension of the ring modulo this ideal.
        """
        try:
            return self.__dimension
        except AttributeError:
            self.__dimension = Integer(self._singular_().std().dim())
        return self.__dimension

    def _singular_groebner_basis(self, algorithm="groebner"):
        """
        Return a Groebner basis of this ideal. If a groebner basis for
        this ideal has been calculated before the cached groebner
        basis is returned regardless of the requested algorithm.

        ALGORITHM: Uses Singular.

        INPUT:
            algorithm -- 'groebner' - use Singular's groebner heuristic to choose
                                      an algorithm (default)
                         'std'      - Buchberger's algorithm
                         'stdhilb'  - computes the standard basis of the homogeneous
                                      ideal in the basering, via a Hilbert driven
                                      standard basis computation.
                         'slimgb'   - SlimGB algorithm

        EXAMPLES:

        We compute a Groebner basis of "cyclic 4" relative to
        lexicographic ordering.

            sage: R = PolynomialRing(RationalField(), 4, ['a','b','c','d'], 'lex')
            sage: a,b,c,d = R.gens()
            sage: I = sage.rings.ideal.Cyclic(R,4)
            sage: I
            Ideal (d + c + b + a, c*d + b*c + a*d + a*b, b*c*d + a*c*d + a*b*d + a*b*c, -1 + a*b*c*d) of Polynomial Ring in a, b, c, d over Rational Field
            sage: I.groebner_basis()
             [1 - d^4 - c^2*d^2 + c^2*d^6, -1*d - c + c^2*d^3 + c^3*d^2, -1*d + d^5 - b + b*d^4, -1*d^2 - d^6 + c*d + c^2*d^4 - b*d^5 + b*c, d^2 + 2*b*d + b^2, d + c + b + a]

        \note{Some Groebner basis calculations crash on 64-bit
        opterons with \SAGE's singular build, but work fine with an
        official binary.  If you download and install a Singular
        binary from the Singular website it will not have this problem
        (you can use it with \SAGE by putting it in local/bin/).}
        """
        try:
            return self.__groebner_basis
        except AttributeError:
            if algorithm=="groebner":
                S = self._singular_().groebner()
            elif algorithm=="std":
                S = self._singular_().std()
            elif algorithm=="slimgb":
                S = self._singular_().slimgb()
            elif algorithm=="stdhilb":
                S = self._singular_().stdhilb()
            else:
                raise TypeError, "cannot understand groebner algorithm"
            R = self.ring()
            self.__groebner_basis = Sequence([R(S[i+1]) for i in range(len(S))], R,
                                             check=False, immutable=True)
        return self.__groebner_basis

    def genus(self):
        """
        Return the genus of the projective curve defined by this
        ideal, which must be 1 dimensional.
        """
        try:
            return self.__genus
        except AttributeError:
            I = self._singular_()
            I.parent().lib('normal.lib')
            self.__genus = Integer(I.genus())
            return self.__genus

    def intersection(self, other):
        """
        Return the intersection of the two ideals.

        EXAMPLES:
            sage: R, (x,y) = PolynomialRing(QQ, 2, 'xy', order='lex').objgens()
            sage: I = x*R
            sage: J = y*R
            sage: I.intersection(J)
            Ideal (x*y) of Polynomial Ring in x, y over Rational Field

        The following simple example illustrates that the product need not equal the intersection.
            sage: I = (x^2, y)*R
            sage: J = (y^2, x)*R
            sage: K = I.intersection(J); K
            Ideal (y^2, x*y, x^2) of Polynomial Ring in x, y over Rational Field
            sage: IJ = I*J; IJ
            Ideal (y^3, x*y, x^2*y^2, x^3) of Polynomial Ring in x, y over Rational Field
            sage: IJ == K
            False
        """
        R = self.ring()
        if not isinstance(other, MPolynomialIdeal_singular_repr) or other.ring() != R:
            raise ValueError, "other must be an ideal in the ring of self, but it isn't."
        I = self._singular_()
        sing = I.parent()
        J = sing(other)
        K = I.intersect(J)
        return R.ideal(K)


    def minimal_associated_primes(self):
        r"""
        OUTPUT:
            list -- a list of prime ideals

        EXAMPLES:
            sage: R, (x,y,z) = PolynomialRing(QQ, 3, 'xyz').objgens()
            sage: p = z^2 + 1; q = z^3 + 2
            sage: I = (p*q^2, y-z^2)*R
            sage: I.minimal_associated_primes ()
            [Ideal (-1*z^2 + y, 2 + z^3) of Polynomial Ring in x, y, z over Rational Field, Ideal (-1*z^2 + y, 1 + z^2) of Polynomial Ring in x, y, z over Rational Field]

        ALGORITHM: Uses Singular.
        """
        I = self._singular_()
        I.parent().lib('primdec.lib')
        M = I.minAssGTZ()
        R = self.ring()
        return [R.ideal(J) for J in M]

    def radical(self):
        r"""
        The radical of this ideal.

        EXAMPLES:
        This is an obviously not radical ideal:
            sage: R, (x,y,z) = PolynomialRing(QQ, 3, 'xyz').objgens()
            sage: I = (x^2, y^3, (x*z)^4 + y^3 + 10*x^2)*R
            sage: I.radical()
            Ideal (y, x) of Polynomial Ring in x, y, z over Rational Field

        That the radical is correct is clear from the Groebner basis.
            sage: I.groebner_basis()
            [x^2, y^3]

        This is the example from the singular manual:
            sage: p = z^2 + 1; q = z^3 + 2
            sage: I = (p*q^2, y-z^2)*R
            sage: I.radical()
            Ideal (z^2 - y, 2 + 2*y + y*z + y^2*z) of Polynomial Ring in x, y, z over Rational Field

        \note{(From Singular manual) A combination of the algorithms
        of Krick/Logar and Kemper is used.  Works also in positive
        characteristic (Kempers algorithm).}

            sage: R,(x,y,z) = PolynomialRing(GF(37), 3, 'xyz').objgens()
            sage: p = z^2 + 1; q = z^3 + 2
            sage: I = (p*q^2, y - z^2)*R
            sage: I.radical()
            Ideal (z^2 + 36*y, 2 + 2*y + y*z + y^2*z) of Polynomial Ring in x, y, z over Finite Field of size 37
        """
        S = self.ring()
        I = self._singular_()
        I.parent().lib('primdec.lib')
        r = I.radical()
        return S.ideal(r)

    def reduce(self, f):
        """
        Reduce an element modulo a standard basis for this ideal.
        This returns 0 if and only if the element is in this ideal.

        EXAMPLES:
            sage: R, (x,y) = PolynomialRing(QQ, 2, 'xy').objgens()
            sage: I = (x^3 + y, y)*R
            sage: I.reduce(y)
            0
            sage: I.reduce(x^3)
            0
            sage: I.reduce(x - y)
            x

            sage: I = (y^2 - (x^3 + x))*R
            sage: I.reduce(x^3)
            y^2 - x
            sage: I.reduce(x^6)
            y^4 - 2*x*y^2 + x^2
            sage: (y^2 - x)^2
            y^4 - 2*x*y^2 + x^2
        """
        try:
            f = self.ring()(f)
            S = singular_default
            I = self._singular_(S)
            g = S(f)
            h = g.reduce(I.std())
            return self.ring()(h)

        except TypeError:

            return f

class MPolynomialIdeal_macaulay2_repr:
    """
    An ideal in a multivariate polynomial ring, which has an underlying
    Macaulay2 ring associated to it.

    EXAMPLES:
        sage: x,y,z,w = PolynomialRing(ZZ, 4, 'xyzw').gens()  # optional
        sage: I = ideal(x*y-z^2, y^2-w^2)       # optional
        sage: I                                 # optional
        Ideal (-1*w^2 + y^2, -1*z^2 + x*y) of Polynomial Ring in x, y, z, w over Integer Ring
    """
    #def __init__(self, ring, gens, coerce=True):
    #    MPolynomialIdeal.__init__(self, ring, gens, coerce=coerce)

    def _macaulay2_(self, macaulay2=None):
        """
        Return Macaulay2 ideal corresponding to this ideal.
        """
        if macaulay2 is None: macaulay2 = macaulay2_default
        try:
            self.ring()._macaulay2_(macaulay2)
            I = self.__macaulay2
            if not (I.parent() is macaulay2):
                raise ValueError
            I._check_valid()
            return I
        except (AttributeError, ValueError):
            self.ring()._macaulay2_(macaulay2)
            gens = [str(x) for x in self.gens()]
            if len(gens) == 0:
                gens = ['0']
            self.__macaulay2 = macaulay2.ideal(gens)
        return self.__macaulay2

    def _macaulay2_groebner_basis(self):
        """
        Return the Groebner basis for this ideal.

        ALGORITHM: Computed using Macaulay2.

        EXAMPLE:
            sage: x,y,z,w = PolynomialRing(ZZ, 4, 'xyzw').gens()      # optional
            sage: I = ideal(x*y-z^2, y^2-w^2)                                         # optional
            sage: I.groebner_basis()                                                  # optional
            [-1*w^2 + y^2, -1*z^2 + x*y, -1*y*z^2 + x*w^2]
        """
        try:
            return self.__groebner_basis
        except AttributeError:
            I = self._macaulay2_()
            G = str(I.gb().generators()).replace('\n','')
            i = G.rfind('{{')
            j = G.rfind('}}')
            G = G[i+2:j].split(',')
            L = self.ring().var_dict()
            B = [sage_eval(f, L) for f in G]
            B.sort()
            self.__groebner_basis = B
            return B



class MPolynomialIdeal( MPolynomialIdeal_singular_repr, MPolynomialIdeal_macaulay2_repr, Ideal_generic ):
    """
    An ideal of a multivariate polynomial ring.
    """
    def __init__(self, ring, gens, coerce=True):
        """
        Create an ideal in a multivariate polynomial ring.

        EXAMPLES:
            sage: R = PolynomialRing(IntegerRing(), 2, ['x','y'], order='lex'); x,y = R.gens()
            sage: R.ideal([x, y])
            Ideal (y, x) of Polynomial Ring in x, y over Integer Ring
            sage: R = PolynomialRing(GF(3), 2); x = R.gens()
            sage: R.ideal([x[0]**2, x[1]**3])
            Ideal (x0^2, x1^3) of Polynomial Ring in x0, x1 over Finite Field of size 3
        """
        Ideal_generic.__init__(self, ring, gens, coerce=coerce)

    def groebner_fan(self, is_groebner_basis=False, symmetry=None, verbose=False):
        r"""
        Return the Groebner fan of this ideal.

        The base ring must be $\Q$ or a finite field $\F_p$ of with
        $p \leq 32749$.

        INPUT:
            is_groebner_basis -- bool (default False).  if True, then I.gens() must be
                                 a Groebner basis with respect to the standard
                                 degree lexicographic term order.
            symmetry -- default: None; if not None, describes symmetries of the ideal
            verbose -- default: False; if True, printout useful info during computations
        """
        import groebner_fan
        return groebner_fan.GroebnerFan(self, is_groebner_basis=is_groebner_basis,
                                        symmetry=symmetry, verbose=verbose)

    def groebner_basis(self, algorithm="singular:groebner"):
        """
        Return a Groebner basis of this ideal.

        INPUT:
            algorithm -- determines the algorithm to use, available are:
                         * None - autoselect (default)
                         * 'singular:groebner' - Singular's groebner command
                         * 'singular:std' - Singular's std command
                         * 'singular:stdhilb' - Singular's stdhib command
                         * 'singular:slimgb' - Singular's slimgb command
                         * 'macaulay2:gb' (if available) - Macaulay2's gb command

        ALGORITHM: Uses Singular or Macaulay2 (if available)

        """
        if algorithm.startswith('singular:'):
            return self._singular_groebner_basis(algorithm[9:])
        elif algorithm == 'macaulay2:gb':
            return self._macaulay2_groebner_basis()
        elif algorithm == None:
            if self.ring() == ZZ:
                return self._macaulay2_groebner_basis()
            else:
                return self._singular_groebner_basis()
        else:
            raise TypeError, "cannot understand groebner algorithm"

    #def is_homogeneous(self):
    #    try:
    #        return self.__is_homogeneous
    #    except AttributeError:

