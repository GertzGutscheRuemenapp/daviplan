/**
 * derived from https://material.angular.io/components/tree/api
 */

import {SelectionModel} from '@angular/cdk/collections';
import {FlatTreeControl} from '@angular/cdk/tree';
import { Component, EventEmitter, Injectable, Input, OnInit, Output } from '@angular/core';
import {MatTreeFlatDataSource, MatTreeFlattener} from '@angular/material/tree';
import {BehaviorSubject} from 'rxjs';

/**
 * Node for to-do item
 */
export class TreeItemNode {
  id?: number | string;
  children?: TreeItemNode[];
  name!: string;
}

/** Flat to-do item node with expandable and level information */
export class TreeItemFlatNode {
  id?: number | string;
  name!: string;
  level!: number;
  expandable!: boolean;
  isSelected: boolean = false;
}

/**
 * Checklist database, it can build a tree structured Json object.
 * Each node in Json object represents a to-do item or a category.
 * If a node is a category, it has children items and new items can be added under the category.
 */
@Injectable({ providedIn: 'root' })
export class ChecklistDatabase {
  dataChange = new BehaviorSubject<TreeItemNode[]>([]);
  get data(): TreeItemNode[] { return this.dataChange.value; }

  constructor() {}

  initialize(items: TreeItemNode[]) {
    // Build the tree nodes from Json object. The result is a list of `TodoItemNode` with nested
    //     file node as children.
    const data = items;//this.buildFileTree(items, 0);
    // Notify the change.
    this.dataChange.next(data);
  }

  /**
   * Build the file structure tree. The `value` is the Json object, or a sub-tree of a Json object.
   * The return value is the list of `TodoItemNode`.
   */
  buildFileTree(obj: {[key: string]: any}, level: number): TreeItemNode[] {
    return Object.keys(obj).reduce<TreeItemNode[]>((accumulator, key) => {
      const value = obj[key];
      const node = new TreeItemNode();
      node.name = key;

      if (value != null) {
        if (typeof value === 'object') {
          node.children = this.buildFileTree(value, level + 1);
        } else {
          node.name = value;
        }
      }

      return accumulator.concat(node);
    }, []);
  }

  /** Add an item to to-do list */
  insertItem(child: TreeItemNode, parent: TreeItemNode | undefined = undefined ) {
    if (!parent) return;
    if (parent.children) {
      parent.children.push();
      this.dataChange.next(this.data);
    }
  }
  refresh(): void{
    this.dataChange.next(this.data);
  }
}

@Component({
  selector: 'app-check-tree',
  templateUrl: './check-tree.component.html',
  styleUrls: ['./check-tree.component.scss']
})
export class CheckTreeComponent implements OnInit {
  @Input() items: TreeItemNode[] = [];
  @Input() expandOnClick: boolean = false;
  @Input() addItemTitle: string = '';
  @Output() itemSelected = new EventEmitter<TreeItemNode>();
  @Output() addItemClicked = new EventEmitter<TreeItemNode>();
  @Output() itemChecked = new EventEmitter<{ item: TreeItemNode, checked: boolean }>();
  /** Map from flat node to nested node. This helps us finding the nested node to be modified */
  flatNodeMap = new Map<TreeItemFlatNode, TreeItemNode>();
  /** Map from nested node to flattened node. This helps us to keep the same object for selection */
  nestedNodeMap = new Map<TreeItemNode, TreeItemFlatNode>();

  treeControl!: FlatTreeControl<TreeItemFlatNode>;
  treeFlattener!: MatTreeFlattener<TreeItemNode, TreeItemFlatNode>;
  dataSource!: MatTreeFlatDataSource<TreeItemNode, TreeItemFlatNode>;

  /** The selection for checklist */
  checklistSelection = new SelectionModel<TreeItemFlatNode>(true );

  constructor(private _database: ChecklistDatabase) { }

  ngOnInit(): void {
    this._database.initialize(this.items);
    this.treeFlattener = new MatTreeFlattener(this.transformer, this.getLevel,
      this.isExpandable, this.getChildren);
    this.treeControl = new FlatTreeControl<TreeItemFlatNode>(this.getLevel, this.isExpandable);
    this.dataSource = new MatTreeFlatDataSource(this.treeControl, this.treeFlattener);

    this._database.dataChange.subscribe(data => {
      this.dataSource.data = data;
    });
  }

  setItems(items: TreeItemNode[]): void {
    this.items = items;
    this._database.initialize(items);
    const _this = this;
  }

  addChild(parent: TreeItemNode, child: TreeItemNode) {
    this._database.insertItem(child, parent);
  }

  refresh(): void {
    this._database.refresh();
  }

  getLevel = (node: TreeItemFlatNode) => node.level;
  isExpandable = (node: TreeItemFlatNode) => node.expandable;
  getChildren = (node: TreeItemNode): TreeItemNode[] | undefined => node.children;
  hasChild = (_: number, _nodeData: TreeItemFlatNode) => _nodeData.expandable;

  /**
   * Transformer to convert nested node to flat node. Record the nodes in maps for later use.
   */
  transformer = (node: TreeItemNode, level: number) => {
    const existingNode = this.nestedNodeMap.get(node);
    const flatNode = existingNode && existingNode.name === node.name
      ? existingNode
      : new TreeItemFlatNode();
    flatNode.name = node.name;
    flatNode.level = level;
    flatNode.id = node.id;
    flatNode.expandable = !!node.children;
    this.flatNodeMap.set(flatNode, node);
    this.nestedNodeMap.set(node, flatNode);
    return flatNode;
  }

  /** Whether all the descendants of the node are selected. */
  descendantsAllSelected(node: TreeItemFlatNode): boolean {
    const descendants = this.treeControl.getDescendants(node);
    const descAllSelected = descendants.length > 0 && descendants.every(child => {
      return this.checklistSelection.isSelected(child);
    });
    return descAllSelected;
  }

  /** Whether part of the descendants are selected */
  descendantsPartiallySelected(node: TreeItemFlatNode): boolean {
    const descendants = this.treeControl.getDescendants(node);
    const result = descendants.some(child => this.checklistSelection.isSelected(child));
    return result && !this.descendantsAllSelected(node);
  }

  /** Toggle the item selection. Select/deselect all the descendants node */
  itemSelectionToggle(flatNode: TreeItemFlatNode): void {
    this.checklistSelection.toggle(flatNode);
    const descendants = this.treeControl.getDescendants(flatNode);
    this.checklistSelection.isSelected(flatNode)
      ? this.checklistSelection.select(...descendants)
      : this.checklistSelection.deselect(...descendants);

    descendants.forEach(child => {
      const isSelected = this.checklistSelection.isSelected(child);
      const node = this.flatNodeMap.get(child)!;
    });
    this.checkAllParentsSelection(flatNode);
    const node = this.flatNodeMap.get(flatNode)!;
    const isSelected = this.checklistSelection.isSelected(flatNode);
    this.itemChecked.emit({ item: node, checked: isSelected });
  }

  /** Toggle a leaf item selection. Check all the parents to see if they changed */
  leafItemSelectionToggle(flatNode: TreeItemFlatNode): void {
    this.checklistSelection.toggle(flatNode);
    this.checkAllParentsSelection(flatNode);
    const node = this.flatNodeMap.get(flatNode)!;
    const isSelected = this.checklistSelection.isSelected(flatNode);
    this.itemChecked.emit({ item: node, checked: isSelected });
  }

  /* Checks all the parents when a leaf node is selected/unselected */
  checkAllParentsSelection(node: TreeItemFlatNode): void {
    let parent: TreeItemFlatNode | null = this.getParentNode(node);
    while (parent) {
      this.checkRootNodeSelection(parent);
      parent = this.getParentNode(parent);
    }
  }

  /** Check root node checked state and change it accordingly */
  checkRootNodeSelection(node: TreeItemFlatNode): void {
    const nodeSelected = this.checklistSelection.isSelected(node);
    const descendants = this.treeControl.getDescendants(node);
    const descAllSelected = descendants.length > 0 && descendants.every(child => {
      return this.checklistSelection.isSelected(child);
    });
    if (nodeSelected && !descAllSelected) {
      this.checklistSelection.deselect(node);
    } else if (!nodeSelected && descAllSelected) {
      this.checklistSelection.select(node);
    }
  }

  /* Get the parent node of a node */
  getParentNode(node: TreeItemFlatNode): TreeItemFlatNode | null {
    const currentLevel = this.getLevel(node);

    if (currentLevel < 1) {
      return null;
    }

    const startIndex = this.treeControl.dataNodes.indexOf(node) - 1;

    for (let i = startIndex; i >= 0; i--) {
      const currentNode = this.treeControl.dataNodes[i];

      if (this.getLevel(currentNode) < currentLevel) {
        return currentNode;
      }
    }
    return null;
  }

  setChecked(node: TreeItemFlatNode | TreeItemNode, checked: boolean) {
    let flatNode: TreeItemFlatNode | undefined = (!(node instanceof TreeItemFlatNode)) ? this.nestedNodeMap.get(node) : node;
    if (!flatNode) return;
    if (checked)
      this.checklistSelection.select(flatNode);
    else
      this.checklistSelection.deselect(flatNode);
  }

  select(node: TreeItemFlatNode | TreeItemNode) {
    let flatNode: TreeItemFlatNode | undefined = (!(node instanceof TreeItemFlatNode)) ? this.nestedNodeMap.get(node) : node;
    if (!flatNode) return;
    for (let n of this.flatNodeMap.keys()){
      n.isSelected = flatNode === n;
    }
    if(this.expandOnClick && this.isExpandable(flatNode)) {
      if (this.treeControl.isExpanded(flatNode))
        this.treeControl.collapse(flatNode);
      else
        this.treeControl.expand(flatNode);
    }
    this.itemSelected.emit(this.flatNodeMap.get(flatNode));
  }

  _onAddItemClicked(flatNode: TreeItemFlatNode) {
    this.addItemClicked.emit(this.flatNodeMap.get(flatNode));
  }
}

