#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv)
{
	int i = 0;
	int j = atoi(argv[1]);
	while (i < j)
	{
		sleep(1);
		i++;
	}
	return (0);
}
