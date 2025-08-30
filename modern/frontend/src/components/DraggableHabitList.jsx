import React, { useState } from 'react';
import {
    DndContext,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
} from '@dnd-kit/core';
import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import {
    useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { LoadingSpinner } from './ui/loading';
import { GripVertical, Check, X, Edit } from 'lucide-react';

const SortableHabitItem = ({ habit, onComplete, onEdit, onDelete }) => {
    const [isCompleting, setIsCompleting] = useState(false);

    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id: habit.id });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
    };

    const handleComplete = async () => {
        setIsCompleting(true);
        await onComplete(habit.id);
        setIsCompleting(false);
    };

    return (
        <div ref={setNodeRef} style={style} {...attributes}>
            <Card className={`transition-all duration-200 ${isDragging ? 'shadow-2xl scale-105' : 'hover:shadow-lg'}`}>
                <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            {/* Drag Handle */}
                            <div
                                {...listeners}
                                className="cursor-grab active:cursor-grabbing p-1 hover:bg-purple-500/20 rounded transition-colors"
                            >
                                <GripVertical className="w-4 h-4 text-slate-400 hover:text-purple-300" />
                            </div>

                            {/* Habit Info */}
                            <div className="text-2xl">{habit.icon || '⭐'}</div>
                            <div className="flex-1">
                                <h4 className="font-medium text-purple-200">{habit.name}</h4>
                                <p className="text-sm text-slate-400">{habit.description}</p>
                                {habit.streak > 0 && (
                                    <p className="text-sm text-orange-400">🔥 {habit.streak} day streak</p>
                                )}
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex items-center space-x-2">
                            <Button
                                onClick={handleComplete}
                                disabled={isCompleting || habit.completed_today}
                                variant={habit.completed_today ? "secondary" : "magical"}
                                size="sm"
                            >
                                {isCompleting ? (
                                    <LoadingSpinner size="sm" />
                                ) : habit.completed_today ? (
                                    <><Check className="w-4 h-4 mr-1" /> Done</>
                                ) : (
                                    <>✨ Complete</>
                                )}
                            </Button>
                            <Button
                                onClick={() => onEdit(habit)}
                                variant="ghost"
                                size="sm"
                            >
                                <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                                onClick={() => onDelete(habit.id)}
                                variant="destructive"
                                size="sm"
                            >
                                <X className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

const DraggableHabitList = ({ habits, onHabitsReorder, onComplete, onEdit, onDelete, loading }) => {
    const [localHabits, setLocalHabits] = useState(habits);

    React.useEffect(() => {
        setLocalHabits(habits);
    }, [habits]);

    const sensors = useSensors(
        useSensor(PointerSensor),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    const handleDragEnd = (event) => {
        const { active, over } = event;

        if (active.id !== over?.id) {
            const oldIndex = localHabits.findIndex(habit => habit.id === active.id);
            const newIndex = localHabits.findIndex(habit => habit.id === over.id);

            const newOrder = arrayMove(localHabits, oldIndex, newIndex);
            setLocalHabits(newOrder);

            // Update backend with new order
            onHabitsReorder(newOrder.map((habit, index) => ({
                id: habit.id,
                order: index
            })));
        }
    };

    if (loading) {
        return (
            <div className="space-y-4">
                {[1, 2, 3].map(i => (
                    <Card key={i} className="animate-pulse">
                        <CardContent className="p-4">
                            <div className="h-16 bg-slate-700 rounded"></div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        );
    }

    if (localHabits.length === 0) {
        return (
            <Card>
                <CardContent className="p-8 text-center">
                    <div className="text-6xl mb-4">📜</div>
                    <p className="text-slate-400">No spells to organize yet!</p>
                </CardContent>
            </Card>
        );
    }

    return (
        <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
        >
            <SortableContext items={localHabits} strategy={verticalListSortingStrategy}>
                <div className="space-y-4">
                    {localHabits.map((habit) => (
                        <SortableHabitItem
                            key={habit.id}
                            habit={habit}
                            onComplete={onComplete}
                            onEdit={onEdit}
                            onDelete={onDelete}
                        />
                    ))}
                </div>
            </SortableContext>
        </DndContext>
    );
};

export default DraggableHabitList;
