#ifndef A90_CHANGELOG_H
#define A90_CHANGELOG_H

#include <stddef.h>

#define A90_CHANGELOG_MAX_ENTRIES 96
#define A90_CHANGELOG_DETAIL_MAX 5

struct a90_changelog_entry {
    const char *label;
    const char *summary;
    const char *details[A90_CHANGELOG_DETAIL_MAX];
};

size_t a90_changelog_count(void);
const struct a90_changelog_entry *a90_changelog_entry_at(size_t index);
size_t a90_changelog_detail_count(const struct a90_changelog_entry *entry);

#endif
