#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>

int main(int argc, char **argv, char** envp)
{
	sleep(atoi(argv[1]));
	return (atoi(argv[2]));
}
