from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from functools import partial

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import compas

from compas.utilities import hex_to_rgb
from compas.utilities import flatten

from compas.viewers.core import GLWidget
from compas.viewers.core import Grid
from compas.viewers.core import Axes


__all__ = ['View']


hex_to_rgb = partial(hex_to_rgb, normalize=True)


def flist(items):
    return list(flatten(items))


class View(GLWidget):
    """"""

    def __init__(self, controller):
        super(View, self).__init__()
        self.controller = controller
        self.n = 0
        self.v = 0
        self.e = 0
        self.f = 0

    @property
    def assembly(self):
        return self.controller.assembly

    @property
    def blocks(self):
        return self.controller.blocks

    @property
    def settings(self):
        return self.controller.settings

    # ==========================================================================
    # arrays
    # ==========================================================================

    # @property
    # def array_xyz(self):
    #     xyz = []
    #     for block in self.blocks:
    #         xyz += block.xyz
    #     return flist(xyz)

    # @property
    # def array_vertices(self):
    #     vertices = []
    #     for block in self.blocks:
    #         i = len(vertices)
    #         vertices += [key + i for key in block.vertices]
    #     return vertices

    # @property
    # def array_edges(self):
    #     i = 0
    #     edges = []
    #     for block in self.blocks:
    #         edges += [[u + i, v + i] for u, v in block.edges]
    #         i += len(list(block.vertices))
    #     return flist(edges)

    # @property
    # def array_faces_front(self):
    #     i = 0
    #     faces = []
    #     for block in self.blocks:
    #         faces += [[u + i for u in face] for face in block.faces]
    #         i += len(list(block.vertices))
    #     return flist(faces)

    # @property
    # def array_faces_back(self):
    #     i = 0
    #     faces = []
    #     for block in self.blocks:
    #         faces += [[u + i for u in face] for face in block.faces]
    #         i += len(list(block.vertices))
    #     return flist(face[::-1] for face in faces)

    # @property
    # def array_vertices_color(self):
    #     return flist(hex_to_rgb(self.settings['vertices.color']) for _ in self.array_vertices)

    # @property
    # def array_edges_color(self):
    #     return flist(hex_to_rgb(self.settings['edges.color']) for _ in self.array_vertices)

    # @property
    # def array_faces_color_front(self):
    #     return flist(hex_to_rgb(self.settings['faces.color:front']) for _ in self.array_xyz)

    # @property
    # def array_faces_color_back(self):
    #     return flist(hex_to_rgb(self.settings['faces.color:back']) for _ in self.array_xyz)

    def block_array_xyz(self, block):
        return flist(block.xyz)

    def block_array_vertices(self, block):
        return list(block.vertices)

    def block_array_edges(self, block):
        return flist(block.edges)

    def block_array_faces_front(self, block):
        return flist(block.faces)

    def block_array_faces_back(self, block):
        return flist(face[::-1] for face in block.faces)

    def block_array_vertices_color(self, block):
        return flist(hex_to_rgb(self.settings['vertices.color']) for key in block.vertices)

    def block_array_edges_color(self, block):
        return flist(hex_to_rgb(self.settings['edges.color']) for key in block.vertices)

    def block_array_faces_color_front(self, block):
        return flist(hex_to_rgb(self.settings['faces.color:front']) for key in block.xyz)

    def block_array_faces_color_back(self, block):
        return flist(hex_to_rgb(self.settings['faces.color:back']) for key in block.xyz)

    # ==========================================================================
    # CAD
    # ==========================================================================

    def setup_grid(self):
        grid = Grid()
        index = glGenLists(1)
        glNewList(index, GL_COMPILE)
        grid.draw()
        glEndList()
        self.display_lists.append(index)

    def setup_axes(self):
        axes = Axes()
        index = glGenLists(1)
        glNewList(index, GL_COMPILE)
        axes.draw()
        glEndList()
        self.display_lists.append(index)

    # ==========================================================================
    # painting
    # ==========================================================================

    def paint(self):
        glDisable(GL_DEPTH_TEST)
        for dl in self.display_lists:
            glCallList(dl)

        glEnable(GL_DEPTH_TEST)
        self.draw_buffers()

    def make_buffers(self):
        self.buffers = []
        for block in self.blocks:
            self.buffers.append({
                'xyz'              : self.make_vertex_buffer(self.block_array_xyz(block)),
                'vertices'         : self.make_index_buffer(self.block_array_vertices(block)),
                'edges'            : self.make_index_buffer(self.block_array_edges(block)),
                'faces:front'      : self.make_index_buffer(self.block_array_faces_front(block)),
                'faces:back'       : self.make_index_buffer(self.block_array_faces_back(block)),
                'vertices.color'   : self.make_vertex_buffer(self.block_array_vertices_color(block), dynamic=True),
                'edges.color'      : self.make_vertex_buffer(self.block_array_edges_color(block), dynamic=True),
                'faces.color:front': self.make_vertex_buffer(self.block_array_faces_color_front(block), dynamic=True),
                'faces.color:back' : self.make_vertex_buffer(self.block_array_faces_color_back(block), dynamic=True),
                'n'                : len(self.block_array_xyz(block)),
                'v'                : len(self.block_array_vertices(block)),
                'e'                : len(self.block_array_edges(block)),
                'f'                : len(self.block_array_faces_front(block)),
            })

    def draw_buffers(self):
        if not self.buffers:
            return

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

        for b in self.buffers:

            glBindBuffer(GL_ARRAY_BUFFER, b['xyz'])
            glVertexPointer(3, GL_FLOAT, 0, None)

            if self.settings['faces.on']:
                glBindBuffer(GL_ARRAY_BUFFER, b['faces.color:front'])
                glColorPointer(3, GL_FLOAT, 0, None)
                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, b['faces:front'])
                glDrawElements(GL_TRIANGLES, b['f'], GL_UNSIGNED_INT, None)

                glBindBuffer(GL_ARRAY_BUFFER, b['faces.color:back'])
                glColorPointer(3, GL_FLOAT, 0, None)
                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, b['faces:back'])
                glDrawElements(GL_TRIANGLES, b['f'], GL_UNSIGNED_INT, None)

            if self.settings['edges.on']:
                glLineWidth(self.settings['edges.width:value'])
                glBindBuffer(GL_ARRAY_BUFFER, b['edges.color'])
                glColorPointer(3, GL_FLOAT, 0, None)
                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, b['edges'])
                glDrawElements(GL_LINES, b['e'], GL_UNSIGNED_INT, None)

            if self.settings['vertices.on']:
                glPointSize(self.settings['vertices.size:value'])
                glBindBuffer(GL_ARRAY_BUFFER, b['vertices.color'])
                glColorPointer(3, GL_FLOAT, 0, None)
                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, b['vertices'])
                glDrawElements(GL_POINTS, b['v'], GL_UNSIGNED_INT, None)

        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

    pass