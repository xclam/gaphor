"""
This is the TreeView that is most common (for example: it is used
in Rational Rose). This is a tree based on namespace relationships. As
a result only classifiers are shown here.
"""

import gobject
import gtk
import operator
import stock

from zope import component

from gaphor import UML
from gaphor.UML.event import ModelFactoryEvent, FlushFactoryEvent
from gaphor.UML.interfaces import IAttributeChangeEvent, IElementCreateEvent, IElementDeleteEvent
from gaphor.UML.event import DerivedUnionSetEvent
from gaphor.transaction import Transaction


# The following items will not be shown in the treeview, although they
# are UML.Namespace elements.
_default_filter_list = (
    UML.Class,
    UML.Package,
    UML.Diagram,
    UML.Profile,
    UML.Stereotype,
    UML.Property,
    UML.Operation
    )

# TODO: update tree sorter:
# Diagram before Class & Package.
# Property before Operation
_tree_sorter = operator.attrgetter('name')


class NamespaceModel(gtk.GenericTreeModel):
    """
    The NamespaceModel holds a view on the data model based on namespace
    relationships (such as a Package containing a Class).

    NamedElement.namespace[1] -- Namespace.ownedMember[*]

    NOTE: when a model is loaded no IAssociation*Event's are emitted.
    
    """


    def __init__(self, factory):
        # Init parent:
        gtk.GenericTreeModel.__init__(self)

        # We own the references to the iterators.
        self.set_property ('leak_references', 0)

        self.factory = factory

        self._nodes = { None: [] }

        self.filter = _default_filter_list

        component.provideHandler(self.flush)
        component.provideHandler(self.refresh)
        component.provideHandler(self._on_element_change)
        component.provideHandler(self._on_element_create)
        component.provideHandler(self._on_element_delete)
        component.provideHandler(self._on_association_set)

        self._build_model()

    def path_from_element(self, e):
        if e:
            ns = e.namespace
            n = self._nodes[ns]
            return self.path_from_element(ns) + (n.index(e),)
        else:
            return ()

    def element_from_path(self, path):
        """
        Get the node form a path. None is returned if no node is found.
        """
        try:
            nodes = self._nodes
            node = None
            for index in path:
                node = nodes[node][index]
            return node
        except IndexError:
            return None

    @component.adapter(IAttributeChangeEvent)
    def _on_element_change(self, event):
        """
        Element changed, update appropriate row.
        """
        element = event.element
        if element not in self._nodes:
            return

        if event.property is UML.Classifier.isAbstract or \
                event.property is UML.BehavioralFeature.isAbstract:
            path = self.path_from_element(element)
            if path:
                self.row_changed(path, self.get_iter(path))

        if event.property is UML.NamedElement.name:
            path = self.path_from_element(element)
            if not path:
                return
            self.row_changed(path, self.get_iter(path))
            parent_nodes = self._nodes[element.namespace]
            parent_path = self.path_from_element(element.namespace)
            if not parent_path:
                return

            original = list(parent_nodes)
            parent_nodes.sort(key=_tree_sorter)
            if parent_nodes != original:
                # reorder the list:
                self.rows_reordered(parent_path, self.get_iter(parent_path),
                                    map(list.index,
                                        [original] * len(parent_nodes),
                                        parent_nodes))

    def _add_elements(self, element):
        """
        Add a single element.
        """
        self._nodes.setdefault(element, [])
        parent = self._nodes[element.namespace]
        parent.append(element)
        parent.sort(key=_tree_sorter)
        path = self.path_from_element(element)
        self.row_inserted(path, self.get_iter(path))

        # Add children
        if isinstance(element, UML.Namespace):
            for e in element.ownedMember:
                if type(e) in self.filter:
                    self._add_elements(e)


    @component.adapter(IElementCreateEvent)
    def _on_element_create(self, event):
        element = event.element
        if event.service is self.factory and \
                type(element) in self.filter:
            self._add_elements(element)


    @component.adapter(IElementDeleteEvent)
    def _on_element_delete(self, event):
        element = event.element
        if event.service is self.factory and \
                type(element) in self.filter:

            try:
                path = self.path_from_element(element)
            except (KeyError, ValueError):
                # No such element (anymore)
                return

            # Remove element from parent
            if element.namespace:
                parent_nodes = self._nodes[element.namespace]
                parent_nodes.remove(element)

            # Remove all sub-elements:
            def remove(n):
                for c in self._nodes.get(n, []):
                    remove(c)
                del self._nodes[n]

            remove(element)
            if path:
                self.row_deleted(path)


    @component.adapter(DerivedUnionSetEvent)
    def _on_association_set(self, event):
        element = event.element
        if element not in self._nodes:
            return

        if event.property is UML.NamedElement.namespace:
            if not self._nodes.has_key(element):
                return
            old_value, new_value = event.old_value, event.new_value

            # Remove entry from old place
            path = self.path_from_element(old_value) + (self._nodes[old_value].index(element),)
            self._nodes[old_value].remove(element)
            self.row_deleted(path)

            # and add to new place
            parent = self._nodes[element.namespace]
            parent.append(element)
            parent.sort(key=_tree_sorter)
            path = self.path_from_element(element)
            self.row_inserted(path, self.get_iter(path))

    @component.adapter(ModelFactoryEvent)
    def refresh(self, event=None):
        self.flush()
        self._build_model()

    @component.adapter(FlushFactoryEvent)
    def flush(self, event=None):
        for n in self._nodes[None]:
            self.row_deleted((0,))
        self._nodes = {None: []}

    def _build_model(self):
        toplevel = self.factory.select(lambda e: isinstance(e, UML.Namespace) and not e.namespace)

        for element in toplevel:
            self._add_elements(element)

    # TreeModel methods:

    def on_get_flags(self):
        """
        Returns the GtkTreeModelFlags for this particular type of model.
        """
        return 0

    def on_get_n_columns(self):
        """
        Returns the number of columns in the model.
        """
        return 1

    def on_get_column_type(self, index):
        """
        Returns the type of a column in the model.
        """
        return gobject.TYPE_PYOBJECT

    def on_get_path(self, node):
        """
        Returns the path for a node as a tuple (0, 1, 1).
        """
        path = self.path_from_element(node)
        return path

    def on_get_iter(self, path):
        """
        Returns the node corresponding to the given path.
        The path is a tuple of values, like (0 1 1). Returns None if no
        iterator can be created.
        """
        return self.element_from_path(path)

    def on_get_value(self, node, column):
        """
        Returns the model element that matches 'node'.
        """
        assert column == 0, 'column can only be 0'
        return node

    def on_iter_next(self, node):
        """
        Returns the next node at this level of the tree. None if no
        next element.
        """
        try:
            parent = self._nodes[node.namespace]
            index = parent.index(node)
            return parent[index + 1]
        except IndexError, e:
            return None
        
    def on_iter_has_child(self, node):
        """
        Returns true if this node has children, or None.
        """
        return len(self._nodes[node]) > 0

    def on_iter_children(self, node):
        """
        Returns the first child of this node, or None.
        """
        return self._nodes[node][0]

    def on_iter_n_children(self, node):
        """
        Returns the number of children of this node.
        """
        return len(self._nodes[node])

    def on_iter_nth_child(self, node, n):
        """
        Returns the nth child of this node.
        """
        try:
            nodes = self._nodes[node]
            return nodes[n]
        except TypeError, e:
            return None

    def on_iter_parent(self, node):
        """
        Returns the parent of this node or None if no parent
        """
        return node.namespace


class NamespaceView(gtk.TreeView):

    TARGET_STRING = 0
    TARGET_ELEMENT_ID = 1
    DND_TARGETS = [
        ('STRING', 0, TARGET_STRING),
        ('text/plain', 0, TARGET_STRING),
        ('gaphor/element-id', 0, TARGET_ELEMENT_ID)]
    # Can not set signals for some reason...
    #__gsignals__ = { 'drag-drop': 'override',
    #                 'drag-data-get': 'override',
    #                 'drag-data-delete': 'override',
    #                 'drag-data-received': 'override' }

    def __init__(self, model, factory):
        assert isinstance (model, NamespaceModel), 'model is not a NamespaceModel (%s)' % str(model)
        self.__gobject_init__()
        gtk.TreeView.__init__(self, model)
        self.factory = factory
        self.icon_cache = {}

        self.set_property('headers-visible', False)
        self.set_property('search-column', 0)
        def search_func(model, column, key, iter, data=None):
            assert column == 0
            element = model.get_value(iter, column)
            if element.name:
                return not element.name.startswith(key)
        self.set_search_equal_func(search_func)

        self.set_rules_hint(True)
        selection = self.get_selection()
        selection.set_mode(gtk.SELECTION_BROWSE)
        column = gtk.TreeViewColumn ('')
        # First cell in the column is for an image...
        cell = gtk.CellRendererPixbuf ()
        column.pack_start (cell, 0)
        column.set_cell_data_func (cell, self._set_pixbuf, None)
        
        # Second cell if for the name of the object...
        cell = gtk.CellRendererText ()
        #cell.set_property ('editable', 1)
        cell.connect('edited', self._text_edited)
        column.pack_start (cell, 0)
        column.set_cell_data_func (cell, self._set_text, None)

        assert len (column.get_cell_renderers()) == 2
        self.append_column (column)

        # DND info:
        # drag
        self.enable_model_drag_source(gtk.gdk.BUTTON1_MASK,
                             [NamespaceView.DND_TARGETS[-1]],
                             gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
        self.drag_source_set(gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                             NamespaceView.DND_TARGETS,
                             gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_LINK)
        self.connect('drag-data-get', NamespaceView.on_drag_data_get)

        # drop
        #self.drag_dest_set (gtk.DEST_DEFAULT_ALL, [NamespaceView.DND_TARGETS[-1]],
        #                    gtk.gdk.ACTION_DEFAULT)
        self.enable_model_drag_dest([NamespaceView.DND_TARGETS[-1]],
                                    gtk.gdk.ACTION_DEFAULT)
        self.connect('drag-data-received', NamespaceView.on_drag_data_received)
        self.connect('drag-drop', NamespaceView.on_drag_drop)
        self.connect('drag-data-delete', NamespaceView.on_drag_data_delete)

    def get_selected_element(self):
        selection = self.get_selection()
        model, iter = selection.get_selected()
        if not iter:
            return
        return model.get_value(iter, 0)

    def expand_root_nodes(self):
        self.expand_row((0,), False)

    def _set_pixbuf(self, column, cell, model, iter, data):
        value = model.get_value(iter, 0)
        try:
            icon = self.icon_cache[type(value)]
        except KeyError:
            stock_id = stock.get_stock_id(type(value))
            if stock_id:
                icon = self.render_icon(stock_id, gtk.ICON_SIZE_MENU, '')
            else:
                icon = None
            self.icon_cache[type(value)] = icon
        cell.set_property('pixbuf', icon)


    def _set_text(self, column, cell, model, iter, data):
        """
        Set font and of model elements in tree view.
        """
        value = model.get_value(iter, 0)
        text = value and (value.name or '').replace('\n', ' ') or '&lt;None&gt;'

        if isinstance(value, UML.Diagram):
            text = '<b>%s</b>' % text
        elif (isinstance(value, UML.Classifier) 
                or isinstance(value, UML.Operation)) and value.isAbstract:
            text = '<i>%s</i>' % text

        cell.set_property('markup', text)


    def _text_edited(self, cell, path_str, new_text):
        """
        The text has been edited. This method updates the data object.
        Note that 'path_str' is a string where the fields are separated by
        colons ':', like this: '0:1:1'. We first turn them into a tuple.
        """
        try:
            model = self.get_property('model')
            iter = model.get_iter_from_string(path_str)
            element = model.get_value(iter, 0)
            tx = Transaction()
            element.name = new_text
            tx.commit()
        except Exception, e:
            log.error('Could not create path from string "%s"' % path_str)

#    def do_drag_begin (self, context):
#        print 'do_drag_begin'

    def on_drag_data_get(self, context, selection_data, info, time):
        """
        Get the data to be dropped by on_drag_data_received().
        We send the id of the dragged element.
        """
        #log.debug('on_drag_data_get')
        selection = self.get_selection()
        model, iter = selection.get_selected()
        if iter:
            element = model.get_value(iter, 0)
            if info == NamespaceView.TARGET_ELEMENT_ID:
                selection_data.set(selection_data.target, 8, str(element.id))
            else:
                selection_data.set(selection_data.target, 8, element.name)

    def on_drag_data_delete (self, context):
        """
        DnD magic. do not touch.
        """
        self.emit_stop_by_name('drag-data-delete')

    # Drop
    def on_drag_data_received(self, context, x, y, selection, info, time):
        """
        Drop the data send by on_drag_data_get().
        """
        self.emit_stop_by_name('drag-data-received')
        #print 'drag_data_received'
        data = selection.data
        drop_info = self.get_dest_row_at_pos(x, y)
        if drop_info:
            #print 'drop_info', drop_info
            model = self.get_model()
            element = self.factory.lookup(data)
            path, position = drop_info
            iter = model.get_iter(path)
            dest_element = model.get_value(iter, 0)
            assert dest_element
            # Add the item to the parent if it is dropped on the same level,
            # else add it to the item.
            if position in (gtk.TREE_VIEW_DROP_BEFORE, gtk.TREE_VIEW_DROP_AFTER):
                parent_iter = model.iter_parent(iter)
                if parent_iter is None:
                    dest_element = None
                else:
                    dest_element = model.get_value(parent_iter, 0)

            try:
                # Check if element is part of the namespace of dest_element:
                ns = dest_element
                while ns:
                    if ns is element:
                        raise AttributeError
                    ns = ns.namespace

                # Set package. This only works for classifiers, packages and
                # diagrams. Properties and operations should not be moved.
                tx = Transaction()
                if dest_element is None:
                    del element.package
                else:
                    element.package = dest_element
                tx.commit()

            except AttributeError:
                context.drop_finish(False, time)
            else:
                context.drop_finish(True, time)
                # Finally let's try to select the element again.
                path = model.path_from_element(element)
                if len(path) > 1:
                    self.expand_row(path[:-1], False)
                selection = self.get_selection()
                selection.select_path(path)

    def on_drag_drop(self, context, x, y, time):
        """
        DnD magic. do not touch
        """
        self.emit_stop_by_name('drag-drop')
        self.drag_get_data(context, context.targets[-1], time)
        return 1

gobject.type_register(NamespaceModel)
gobject.type_register(NamespaceView)


# vim: sw=4:et:ai
